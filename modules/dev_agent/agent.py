# -*- coding: utf-8 -*-
"""
JARVIS Dev Agent v3.0
Capacidade de manipular arquivos e codigo do PC inteiro.
OpenCode = ferramenta UNICA (CLI interativo).
Brain = fallback se OpenCode falhar.
"""

import os
import ast
import shutil
import subprocess
import threading
from pathlib import Path
from datetime import datetime


# Zonas BLOQUEADAS (nunca toca)
ZONAS_BLOQUEADAS = [
    "C:\\Windows",
    "C:\\Windows\\System32",
    "C:\\Windows\\SysWOW64",
    "C:\\Program Files\\WindowsApps",
]

# Atalhos de pasta
ZONAS = {
    "desktop":    str(Path.home() / "Desktop"),
    "downloads":  str(Path.home() / "Downloads"),
    "documentos": str(Path.home() / "Documents"),
    "documents":  str(Path.home() / "Documents"),
    "musicas":    str(Path.home() / "Music"),
    "videos":     str(Path.home() / "Videos"),
    "imagens":    str(Path.home() / "Pictures"),
    "pictures":   str(Path.home() / "Pictures"),
    "jarvis":     "C:\\Users\\Administrator\\Desktop\\JARVIS",
    "pendrive":   "E:\\Jarvis",
    "trabalho":   str(Path.home() / "Desktop"),
}

PASTA_TRABALHO = str(Path.home() / "Desktop")


def _bloqueado(caminho):
    """Verifica se caminho esta em zona bloqueada."""
    try:
        p = str(Path(caminho).resolve()).upper()
        for zona in ZONAS_BLOQUEADAS:
            if p.startswith(zona.upper()):
                return True
    except Exception:
        return True
    return False


def resolver_zona(texto):
    """Converte 'desktop' -> path real."""
    tl = str(texto).lower().strip()
    for nome, path in ZONAS.items():
        if nome in tl:
            return path
    if ":\\" in texto or texto.startswith("/"):
        return texto
    return texto


class DevAgent:
    """Capacidade do JARVIS de mexer em arquivos e codigo.
    
    Hierarquia de ferramentas:
      1. OpenCode (skill unica - CLI interativo)
      2. Brain (fallback - conversa)
    """

    def __init__(self, callback_voz=None, brain=None):
        self.callback_voz = callback_voz
        self.brain = brain
        self.opencode_ok = self._check_opencode()
        self._ultimo_resultado = ""

        ferramenta = "OpenCode" if self.opencode_ok else "Brain only"
        print(f"[DEVAGENT] Iniciado ({ferramenta})")

    def _check_opencode(self):
        """Verifica se OpenCode CLI esta disponivel."""
        try:
            r = subprocess.run(
                ["opencode", "--version"],
                capture_output=True, text=True, timeout=5, shell=True,
            )
            return r.returncode == 0
        except Exception:
            return False

    def _falar(self, msg):
        if self.callback_voz:
            try:
                self.callback_voz(msg)
            except Exception:
                pass
        print(f"[DEVAGENT] {msg}")

    # ═══ LISTAGEM ═══

    def listar_pasta(self, caminho):
        """Lista arquivos e pastas."""
        caminho = resolver_zona(caminho)
        if not os.path.exists(caminho):
            return {"erro": f"Pasta nao existe: {caminho}"}
        try:
            itens = list(Path(caminho).iterdir())
            pastas = [i for i in itens if i.is_dir()]
            arquivos = [i for i in itens if i.is_file()]
            return {
                "caminho": caminho,
                "total_pastas": len(pastas),
                "total_arquivos": len(arquivos),
                "pastas": [p.name for p in pastas[:20]],
                "arquivos": [
                    {"nome": f.name,
                     "tamanho_kb": round(f.stat().st_size / 1024, 1)}
                    for f in arquivos[:30]
                ],
            }
        except PermissionError:
            return {"erro": "Sem permissao"}
        except Exception as ex:
            return {"erro": str(ex)}

    def ler_arquivo(self, caminho):
        """Le conteudo de arquivo."""
        path = Path(caminho)
        if not path.exists():
            jarvis_path = Path(ZONAS["jarvis"]) / caminho
            if jarvis_path.exists():
                path = jarvis_path
            else:
                return f"Arquivo nao encontrado: {caminho}"
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as ex:
            return f"Erro: {ex}"

    def buscar_arquivos(self, pasta, extensao="", nome_contem=""):
        """Busca arquivos por filtro."""
        pasta = resolver_zona(pasta)
        if not os.path.exists(pasta):
            return []
        encontrados = []
        try:
            for root, dirs, files in os.walk(pasta):
                dirs[:] = [d for d in dirs
                          if not d.startswith(".") and d != "__pycache__"]
                for f in files:
                    ok_ext = (not extensao or
                             f.lower().endswith(extensao.lower()))
                    ok_nome = (not nome_contem or
                              nome_contem.lower() in f.lower())
                    if ok_ext and ok_nome:
                        encontrados.append(os.path.join(root, f))
                    if len(encontrados) >= 100:
                        return encontrados
        except Exception:
            pass
        return encontrados

    # ═══ MOVER/COPIAR ═══

    def mover_arquivo(self, origem, destino):
        """Move arquivo - avisa pra onde foi."""
        origem = resolver_zona(origem)
        destino = resolver_zona(destino)
        if _bloqueado(origem) or _bloqueado(destino):
            return False, "Zona bloqueada, Sir."
        if not os.path.exists(origem):
            return False, f"Origem nao existe: {origem}"
        try:
            if os.path.isdir(destino):
                nome = Path(origem).name
                destino_final = os.path.join(destino, nome)
            else:
                destino_final = destino
                os.makedirs(Path(destino_final).parent, exist_ok=True)
            shutil.move(origem, destino_final)
            msg = f"Movido {Path(origem).name} para {Path(destino_final).parent}"
            self._falar(msg)
            return True, msg
        except Exception as ex:
            return False, f"Erro: {ex}"

    def organizar_downloads(self):
        """Organiza pasta Downloads por tipo."""
        downloads = Path(ZONAS["downloads"])
        CATEGORIAS = {
            "Imagens":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
            "Videos":     [".mp4", ".mkv", ".avi", ".mov", ".webm"],
            "Documentos": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx"],
            "Musicas":    [".mp3", ".wav", ".flac", ".m4a"],
            "Programas":  [".exe", ".msi", ".zip", ".rar", ".7z"],
            "Codigo":     [".py", ".js", ".html", ".css", ".json"],
        }
        movidos = 0
        detalhes = {}
        for arquivo in downloads.iterdir():
            if not arquivo.is_file():
                continue
            ext = arquivo.suffix.lower()
            categoria = "Outros"
            for cat, exts in CATEGORIAS.items():
                if ext in exts:
                    categoria = cat
                    break
            pasta_destino = downloads / categoria
            pasta_destino.mkdir(exist_ok=True)
            destino_final = pasta_destino / arquivo.name
            if destino_final.exists():
                ts = datetime.now().strftime("%H%M%S")
                destino_final = pasta_destino / f"{arquivo.stem}_{ts}{arquivo.suffix}"
            try:
                shutil.move(str(arquivo), str(destino_final))
                movidos += 1
                detalhes[categoria] = detalhes.get(categoria, 0) + 1
            except Exception:
                pass
        if movidos == 0:
            return "Downloads ja esta organizado, Sir."
        resumo = ", ".join(f"{v} {k.lower()}" for k, v in detalhes.items())
        msg = f"Organizei {movidos} arquivos: {resumo}."
        self._falar(msg)
        return msg

    # ═══ ESCRITA ═══

    def escrever_arquivo(self, caminho, conteudo, validar_python=True):
        """Escreve arquivo com backup automatico."""
        if _bloqueado(caminho):
            return False, "Zona bloqueada."
        path = Path(caminho)

        if validar_python and path.suffix == ".py":
            try:
                ast.parse(conteudo)
            except SyntaxError as se:
                return False, f"Sintaxe Python invalida: {se}"

        # Backup
        if path.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = path.parent / "backups_jarvis"
            backup_dir.mkdir(exist_ok=True)
            backup = backup_dir / f"{path.stem}_{ts}{path.suffix}"
            try:
                shutil.copy2(str(path), str(backup))
                print(f"[DEVAGENT] Backup: {backup.name}")
            except Exception:
                pass

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(conteudo, encoding="utf-8")
            linhas = conteudo.count("\n") + 1
            msg = f"Salvo: {path.name} ({linhas} linhas)."
            self._falar(msg)
            return True, msg
        except Exception as ex:
            return False, f"Erro: {ex}"

    # ═══ OPENCODE (SKILL PRIMARIA) ═══

    def _rodar_opencode(self, prompt, cwd=None, timeout=300):
        """Roda OpenCode CLI como skill do Jarvis.
        
        OpenCode eh um agente de codigo autonomo.
        Ele le, modifica e cria arquivos diretamente.
        """
        if not self.opencode_ok:
            return None

        cwd = cwd or ZONAS["jarvis"]
        if not os.path.exists(cwd):
            cwd = ZONAS["jarvis"]

        try:
            print(f"[DEVAGENT] OpenCode trabalhando em: {cwd}")
            # OpenCode CLI: opencode run "prompt" (non-interactive)
            r = subprocess.run(
                ["opencode", "run", prompt],
                capture_output=True, text=True,
                timeout=timeout, cwd=cwd, shell=True,
                encoding="utf-8", errors="replace",
            )
            saida = (r.stdout or "").strip()
            erro = (r.stderr or "").strip()

            if r.returncode == 0 and saida:
                print(f"[DEVAGENT] OpenCode gerou {len(saida)} chars")
                return saida
            elif saida:
                # Mesmo com erro, pode ter saida util
                return saida
            else:
                print(f"[DEVAGENT] OpenCode sem saida: {erro[:200]}")
                return None
        except subprocess.TimeoutExpired:
            print("[DEVAGENT] OpenCode timeout")
            return None
        except Exception as ex:
            print(f"[DEVAGENT] OpenCode erro: {ex}")
            return None

    # ═══ EXECUCAO DE TAREFAS ═══

    def executar_tarefa_codigo(self, descricao, pasta=None):
        """Executa tarefa de codigo com cascata de ferramentas.
        
        Hierarquia:
          1. OpenCode (skill unica)
          2. Brain (fallback)
        """
        tl = descricao.lower()
        eh_jarvis = any(w in tl for w in [
            "jarvis", "engine.py", "router.py", "brain.py",
            "intents.py", "modulo do jarvis", "hud", "orb",
        ])
        pasta_usar = ZONAS["jarvis"] if eh_jarvis else (pasta or PASTA_TRABALHO)

        # PRIMARIO: OpenCode
        if self.opencode_ok:
            self._falar("Usando OpenCode, Sir.")
            resultado = self._rodar_opencode(descricao, cwd=pasta_usar)
            if resultado:
                return resultado
            print("[DEVAGENT] OpenCode falhou, tentando fallback...")

        # FALLBACK: Brain direto
        return self._criar_com_brain(descricao, pasta_destino=pasta_usar)

    def _criar_com_brain(self, descricao, pasta_destino=None):
        """Fallback: pede pro Brain gerar codigo."""
        if not pasta_destino:
            pasta_destino = ZONAS["desktop"]
        pasta_destino = resolver_zona(pasta_destino)

        self._falar("Gerando com Brain, Sir.")
        if self.brain:
            prompt = f"""Crie um codigo Python completo e funcional.
Pedido: {descricao}
Pasta destino: {pasta_destino}

Regras:
- Codigo em Python 3.12, utf-8
- Comentarios em portugues
- Funcional e testavel
- Responda APENAS o codigo, sem markdown"""
            return self.brain.think(prompt, usar_historico=False)
        return "Sem ferramenta disponivel, Sir."

    def analisar_arquivo_codigo(self, caminho):
        """Analisa codigo e sugere melhorias."""
        conteudo = self.ler_arquivo(caminho)
        if conteudo.startswith("Arquivo") or conteudo.startswith("Erro"):
            return conteudo
        path = Path(caminho)
        self._falar(f"Analisando {path.name}.")

        # Tenta OpenCode primeiro
        if self.opencode_ok:
            prompt = f"Analise este codigo Python eliste 3 melhorias concisas:\n\n{conteudo[:4000]}"
            resultado = self._rodar_opencode(prompt, cwd=str(path.parent))
            if resultado:
                return resultado

        # Fallback Brain
        if self.brain:
            return self.brain.think(
                f"Analise este codigo Python (3 melhorias curtas):\n\n{conteudo[:2000]}",
                usar_historico=False
            )
        return "Sem agente disponivel."

    # ═══ INFO ═══

    def espaco_disco(self, drive="C:"):
        try:
            total, usado, livre = shutil.disk_usage(drive)
            return (f"Drive {drive}: {livre/(1024**3):.1f} GB livres de "
                   f"{total/(1024**3):.1f} GB.")
        except Exception as ex:
            return f"Erro: {ex}"

    def listar_drives(self):
        drives = []
        for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letra}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives


# Singleton
_instance = None

def get_dev_agent(callback_voz=None, brain=None):
    global _instance
    if _instance is None:
        _instance = DevAgent(callback_voz=callback_voz, brain=brain)
    return _instance
