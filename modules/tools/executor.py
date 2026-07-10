# -*- coding: utf-8 -*-
"""
JARVIS Tool Executor v3.1
Brain decide ferramentas via JSON. Backup + AST + diff + rollback.
"""

import json
import re
import os
import shutil
import ast
import subprocess
import threading
from pathlib import Path
from datetime import datetime

from utils.logger import print_jarvis, print_system, print_success, print_error
from modules.tools.permissoes import get_permissoes
from modules.tools.aprendizado_proativo import get_aprendizado
from modules.tools.diff_helper import gerar_diff, resumir_diff_voz


def _fazer_backup_executor():
    """Backup automatico do executor antes de carregar."""
    try:
        p = Path(__file__)
        bkp_dir = p.parent / "backups_executor"
        bkp_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = bkp_dir / f"{p.stem}_{ts}{p.suffix}"
        shutil.copy2(str(p), str(destino))
        print_success(f"[EXECUTOR] Backup: {destino.name}")
    except Exception as e:
        print(f"[EXECUTOR] Backup falhou: {e}")

_fazer_backup_executor()

# ═══ PROMPT DE DECISAO ═══
FERRAMENTAS_PROMPT = """FERRAMENTAS DISPONIVEIS:

LEITURA (auto): listar_pasta, ler_arquivo, espaco_disco, listar_drives, analisar_codigo
ESCRITA (auto): criar_codigo, criar_arquivo
AUTOMACAO (auto): mover_arquivo, copiar_arquivo, organizar_downloads, renomear_arquivo, enviar_pelo_discord
SISTEMA (confirma): abrir_programa, fechar_programa, modificar_arquivo, rodar_comando, reiniciar_jarvis, executar_ultimo
CRITICO (dupla confirmacao): deletar_arquivo, deletar_pasta, instalar_programa, executar_shell
OUTROS: conversar, perguntar_mais"""

PROMPT_DECISAO = """Voce e o cerebro do JARVIS. Le a frase do Sir e escolhe UMA ferramenta.

""" + FERRAMENTAS_PROMPT + """

RESPONDA APENAS JSON PURO. Sem markdown. Sem explicacao.

Formato:
{"ferramenta":"nome","args":{...},"fala":"msg curta ao executar","descricao_acao":"resumo"}

Exemplos:

Sir: "tudo bem?"
{"ferramenta":"conversar","args":{"resposta":"Tudo certo, Sir."},"fala":"","descricao_acao":""}

Sir: "cria um jogo snake em python no desktop"
{"ferramenta":"criar_codigo","args":{"descricao":"jogo snake em python","nome_arquivo":"snake.py","pasta":"C:\\Users\\Administrator\\Desktop"},"fala":"Criando snake, Sir.","descricao_acao":"criar snake.py no Desktop"}

Sir: "abre o spotify"
{"ferramenta":"abrir_programa","args":{"nome":"spotify"},"fala":"","descricao_acao":"abrir Spotify"}

Sir: "organiza meus downloads"
{"ferramenta":"organizar_downloads","args":{},"fala":"Organizando.","descricao_acao":"organizar downloads"}

Sir: "quanto espaco tem no C"
{"ferramenta":"espaco_disco","args":{"drive":"C:"},"fala":"","descricao_acao":"verificar espaco C:"}

Sir: "agora executa" / "roda esse script" / "executa o ultimo"
{"ferramenta":"executar_ultimo","args":{},"fala":"Executando.","descricao_acao":"executar ultimo script criado"}

Sir: "deleta a pasta temp"
{"ferramenta":"deletar_pasta","args":{"caminho":"C:\\Users\\Administrator\\Desktop\\temp"},"fala":"","descricao_acao":"deletar pasta temp"}"""

# ═══ PASTAS ═══
PASTA_TRABALHO = Path.home() / "Desktop" / "JarvisCriacoes"

ZONAS = {
    "desktop":         str(Path.home() / "Desktop"),
    "downloads":       str(Path.home() / "Downloads"),
    "documentos":      str(Path.home() / "Documents"),
    "musicas":         str(Path.home() / "Music"),
    "videos":          str(Path.home() / "Videos"),
    "imagens":         str(Path.home() / "Pictures"),
    "jarvis":          "C:\\Users\\Administrator\\Desktop\\JARVIS",
    "jarvis_criacoes": str(PASTA_TRABALHO),
    "pendrive":        "E:\\Jarvis",
}


def resolver_pasta(nome):
    """Resolve alias de pasta para caminho absoluto."""
    if isinstance(nome, str) and nome.lower() in ZONAS:
        return ZONAS[nome.lower()]
    return nome


class ToolExecutor:

    def __init__(self, brain=None, dev_agent=None, callback_voz=None, engine=None):
        self.brain = brain
        self.dev_agent = dev_agent
        self.callback_voz = callback_voz
        self.engine = engine
        self.permissoes = get_permissoes()
        self.aprendizado = get_aprendizado(callback_voz=callback_voz)
        self._ultimo_arquivo_criado = None
        PASTA_TRABALHO.mkdir(exist_ok=True)
        print_success("[TOOLS v3.1] Executor carregado.")

    # ═══ HELPERS ═══

    def _falar(self, msg):
        """Envia mensagem de voz sem bloquear."""
        if self.callback_voz and msg:
            try:
                self.callback_voz(msg)
            except Exception:
                pass

    def _limpar_codigo(self, codigo):
        """Remove markdown e texto explicativo do codigo gerado."""
        if not codigo:
            return ""

        codigo = codigo.strip()

        # Remove blocos markdown ```python ... ```
        match = re.search(r"```(?:python|py)?\s*\n?(.*?)```", codigo, re.DOTALL)
        if match:
            codigo = match.group(1).strip()
        else:
            # Sem markdown - remove linhas explicativas antes do primeiro import/def/print
            linhas = codigo.split("\n")
            inicio = 0
            for i, linha in enumerate(linhas):
                l = linha.strip()
                if (l.startswith(("import ", "from ", "def ", "class ", "print(",
                                  "#", "if ", "for ", "while ", "try:"))
                    or "=" in l[:30]):
                    inicio = i
                    break
            codigo = "\n".join(linhas[inicio:]).strip()

        # Remove ``` perdido no final
        codigo = re.sub(r"\n?```\s*$", "", codigo).strip()
        return codigo

    def _parsear_json(self, texto):
        """Extrai JSON da resposta do Brain."""
        if not texto:
            return None
        texto = texto.strip()
        # Remove markdown
        texto = re.sub(r"^```json\s*", "", texto, flags=re.MULTILINE)
        texto = re.sub(r"^```\s*", "", texto, flags=re.MULTILINE)
        texto = re.sub(r"```$", "", texto, flags=re.MULTILINE)
        # Extrai objeto JSON
        match = re.search(r"\{.*\}", texto, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return None

    # ═══ DECISAO DE FERRAMENTA ═══

    def _decidir_ferramenta(self, frase, contexto_anterior=""):
        """Groq direto - Ollama eh muito lento pra decisao."""
        prompt_user = f'Frase do Sir: "{frase}"'
        if contexto_anterior:
            prompt_user = f"Contexto anterior: {contexto_anterior}\n\n{prompt_user}"

        mensagens = [
            {"role": "system", "content": PROMPT_DECISAO},
            {"role": "user",   "content": prompt_user},
        ]

        # Groq direto (Ollama timeout sempre)
        try:
            from groq import Groq
            groq_key = os.getenv("GROQ_API_KEY", "").strip()
            if not groq_key:
                raise ValueError("Sem GROQ_API_KEY")
            client = Groq(api_key=groq_key)
            print("[TOOLS] Groq decidindo...")
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=mensagens,
                max_tokens=300,
                temperature=0.0,
            )
            content = resp.choices[0].message.content.strip()
            print(f"[TOOLS] Decisao: {content[:80]}")
            return content
        except Exception as ex:
            print_error(f"[TOOLS] Groq falhou: {ex}")

        # Fallback hardcoded
        return '{"ferramenta":"conversar","args":{"resposta":"Nao consegui processar, Sir."},"fala":"","descricao_acao":""}'

    # ═══ PROCESSAMENTO PRINCIPAL ═══

    def processar(self, frase, contexto_anterior=""):
        """Ponto de entrada principal do executor."""
        if not self.brain:
            return "Brain indisponivel."

        # Confirmacao pendente?
        if self.permissoes.tem_pendente():
            status, dados = self.permissoes.processar_resposta(frase)
            if status == "executar":
                return self._executar_confirmado(dados)
            if status in ("pergunta", "cancelado"):
                return dados

        try:
            resposta_raw = self._decidir_ferramenta(frase, contexto_anterior)
            decisao = self._parsear_json(resposta_raw)

            if not decisao:
                print_error(f"[TOOLS] JSON invalido: {resposta_raw[:100]}")
                # Nao inventa - avisa
                if hasattr(self.brain, "think_acao"):
                    return self.brain.think_acao(frase)
                return self.brain.think(frase)

            ferramenta = decisao.get("ferramenta", "conversar")
            args       = decisao.get("args", {})
            fala       = decisao.get("fala", "")
            desc       = decisao.get("descricao_acao", ferramenta)

            print(f"[TOOLS] {ferramenta}({args})")

            # Resolve "ultimo_criado"
            if args.get("caminho_arquivo") == "ultimo_criado":
                args["caminho_arquivo"] = self._ultimo_arquivo_criado or ""

            # Conversa/pergunta nunca pede confirmacao
            if ferramenta in ("conversar", "perguntar_mais"):
                if fala:
                    self._falar(fala)
                return self._executar(ferramenta, args, frase)

            # Verifica permissao
            if self.permissoes.precisa_confirmar(ferramenta, args):
                return self.permissoes.iniciar_confirmacao(ferramenta, args, desc)

            if fala:
                self._falar(fala)

            resultado = self._executar(ferramenta, args, frase)
            self.aprendizado.registrar_acao(ferramenta, args)
            return resultado

        except Exception as ex:
            print_error(f"[TOOLS] Erro geral: {ex}")
            import traceback
            traceback.print_exc()
            return self.brain.think(frase)

    def _executar_confirmado(self, dados):
        """Executa acao apos confirmacao do usuario."""
        ferramenta = dados["ferramenta"]
        args       = dados["args"]
        print(f"[TOOLS] CONFIRMADO: {ferramenta}({args})")
        resultado = self._executar(ferramenta, args, "")
        self.aprendizado.registrar_acao(ferramenta, args)
        return resultado

    def _executar(self, ferramenta, args, frase):
        """Despacha para o metodo _t_ferramenta correspondente."""
        metodo = getattr(self, f"_t_{ferramenta}", None)
        if not metodo:
            return f"Ferramenta desconhecida: {ferramenta}"
        try:
            return metodo(args, frase)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            return f"Erro ao executar {ferramenta}: {ex}"

    # ═══ N1: LEITURA ═══

    def _t_listar_pasta(self, args, frase):
        if not self.dev_agent:
            return "Dev agent indisponivel."
        pasta = resolver_pasta(args.get("pasta", "downloads"))
        r = self.dev_agent.listar_pasta(pasta)
        if "erro" in r:
            return f"Erro: {r['erro']}"
        msg = f"Em {Path(pasta).name}: {r['total_pastas']} pastas, {r['total_arquivos']} arquivos."
        if r.get("arquivos"):
            nomes = ", ".join(a["nome"] for a in r["arquivos"][:5])
            msg += f" Primeiros: {nomes}."
        return msg

    def _t_ler_arquivo(self, args, frase):
        if not self.dev_agent:
            return "Dev agent indisponivel."
        caminho = args.get("caminho", "")
        if not caminho:
            return "Qual arquivo, Sir?"
        conteudo = self.dev_agent.ler_arquivo(caminho)
        print(f"\n=== {caminho} ===\n{conteudo[:2000]}\n===\n")
        return f"Arquivo {Path(caminho).name}: {conteudo.count(chr(10))+1} linhas. Conteudo no terminal."

    def _t_espaco_disco(self, args, frase):
        if not self.dev_agent:
            return "Dev agent indisponivel."
        return self.dev_agent.espaco_disco(args.get("drive", "C:"))

    def _t_listar_drives(self, args, frase):
        if not self.dev_agent:
            return "Dev agent indisponivel."
        return f"Drives: {', '.join(self.dev_agent.listar_drives())}."

    def _t_analisar_codigo(self, args, frase):
        if not self.dev_agent:
            return "Dev agent indisponivel."
        return self.dev_agent.analisar_arquivo_codigo(args.get("caminho", ""))

    # ═══ N2: ESCRITA ═══

    def _gerar_codigo_ollama(self, descricao):
        """Gera codigo via Groq direto - Ollama timeout sempre."""
        prompt = f"""Escreva codigo Python 3.12 COMPLETO e funcional para:

{descricao}

Regras OBRIGATORIAS:
- Codigo COMPLETO e EXECUTAVEL (nao apenas funcao solta)
- Minimo 10 linhas
- Comentarios em portugues
- Use apenas stdlib
- Responda APENAS o codigo Python puro
- NAO use markdown
- NAO escreva explicacao antes nem depois
- Comece DIRETO no codigo"""

        try:
            from groq import Groq
            groq_key = os.getenv("GROQ_API_KEY", "").strip()
            client = Groq(api_key=groq_key)
            print("[CODE] Groq gerando...")
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Voce e um gerador de codigo Python. Responda APENAS codigo puro, sem markdown, sem explicacao."},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=2000,
                temperature=0.2,
            )
            codigo = resp.choices[0].message.content.strip()
            print(f"[CODE] Groq gerou {len(codigo)} chars")
            return self._limpar_codigo(codigo)
        except Exception as ex:
            print_error(f"[CODE GEN] Groq erro: {ex}")
            return f"# Erro ao gerar codigo\nprint('Erro: {ex}')"

    def _t_criar_codigo(self, args, frase):
        """Cria arquivo Python com codigo gerado."""
        descricao = args.get("descricao", frase)
        nome      = args.get("nome_arquivo", "")
        pasta     = resolver_pasta(args.get("pasta", "jarvis_criacoes"))

        print(f"[CODE] Gerando: {descricao[:60]}")
        codigo = self._gerar_codigo_ollama(descricao)
        codigo = self._limpar_codigo(codigo)

        # Valida AST, tenta corrigir uma vez
        for tentativa in range(2):
            try:
                ast.parse(codigo)
                break
            except SyntaxError as se:
                print_error(f"[AST] Tentativa {tentativa+1}: {se}")
                if tentativa == 1:
                    return f"Gerei codigo mas tem erro de sintaxe: {se}"
                print("[AST] Tentando corrigir via Groq...")
                codigo = self.brain.think(
                    f"Corrija APENAS os erros de sintaxe. Retorne so o codigo:\n\n{codigo}",
                    usar_historico=False,
                )
                codigo = self._limpar_codigo(codigo)

        # Define nome do arquivo
        if not nome:
            palavras = re.findall(r"\w+", descricao.lower())[:3]
            nome = "_".join(palavras) + ".py"
        if not nome.endswith(".py"):
            nome += ".py"

        caminho = Path(pasta) / nome
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(codigo, encoding="utf-8")
        self._ultimo_arquivo_criado = str(caminho)

        linhas = codigo.count("\n") + 1
        print_success(f"[CODE] Salvo: {caminho} ({linhas} linhas)")
        return f"Codigo '{nome}' criado em {Path(pasta).name}, Sir. {linhas} linhas."

    def _t_criar_arquivo(self, args, frase):
        """Cria arquivo com conteudo arbitrario."""
        caminho  = args.get("caminho", "")
        conteudo = args.get("conteudo", "")
        if not caminho:
            return "Qual caminho, Sir?"
        try:
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
            Path(caminho).write_text(conteudo, encoding="utf-8")
            self._ultimo_arquivo_criado = caminho
            return f"Criado {Path(caminho).name}, Sir."
        except Exception as ex:
            return f"Erro: {ex}"

    # ═══ N3: AUTOMACAO ═══

    def _t_mover_arquivo(self, args, frase):
        if not self.dev_agent:
            return "Dev agent indisponivel."
        ok, msg = self.dev_agent.mover_arquivo(
            args.get("origem", ""), args.get("destino", "")
        )
        return msg

    def _t_copiar_arquivo(self, args, frase):
        try:
            shutil.copy2(args.get("origem", ""), args.get("destino", ""))
            return "Copiado, Sir."
        except Exception as ex:
            return f"Erro: {ex}"

    def _t_organizar_downloads(self, args, frase):
        if not self.dev_agent:
            return "Dev agent indisponivel."
        return self.dev_agent.organizar_downloads()

    def _t_renomear_arquivo(self, args, frase):
        caminho = args.get("caminho", "")
        novo    = args.get("novo_nome", "")
        try:
            p = Path(caminho)
            p.rename(p.parent / novo)
            return f"Renomeado para {novo}, Sir."
        except Exception as ex:
            return f"Erro: {ex}"

    def _t_enviar_pelo_discord(self, args, frase):
        if not self.engine or not getattr(self.engine, "discord_bot", None):
            return "Discord indisponivel."
        caminho = args.get("caminho_arquivo", "") or self._ultimo_arquivo_criado
        msg     = args.get("mensagem", "Aqui esta, Sir.")
        if not caminho or not Path(caminho).exists():
            return f"Arquivo nao existe: {caminho}"
        try:
            discord_bot = self.engine.discord_bot
            if hasattr(discord_bot, "enviar_arquivo_sync"):
                ok = discord_bot.enviar_arquivo_sync(caminho, msg)
                return f"Enviei {Path(caminho).name} pelo Discord." if ok else "Falhou."
            return "Bot Discord sem metodo enviar_arquivo_sync."
        except Exception as ex:
            return f"Erro: {ex}"

    # ═══ N4: SISTEMA ═══

    def _t_abrir_programa(self, args, frase):
        nome = args.get("nome", "")
        if not nome:
            return "Qual programa, Sir?"
        # Tenta app_launcher primeiro
        if self.engine and hasattr(self.engine, "app_launcher") and self.engine.app_launcher:
            r = self.engine.app_launcher.abrir(nome)
            if r is True:
                return f"Abrindo {nome}, Sir."
            if isinstance(r, str):
                return r
        # Fallback shell
        try:
            subprocess.Popen(f"start {nome}", shell=True)
            return f"Abrindo {nome}, Sir."
        except Exception as ex:
            return f"Erro: {ex}"

    def _t_fechar_programa(self, args, frase):
        nome = args.get("nome", "")
        if not nome.endswith(".exe"):
            nome += ".exe"
        try:
            subprocess.run(
                f"taskkill /f /im {nome}", shell=True, capture_output=True
            )
            return f"Fechei {nome}, Sir."
        except Exception as ex:
            return f"Erro: {ex}"

    def _t_modificar_arquivo(self, args, frase):
        """Modifica arquivo existente com backup + AST + diff."""
        caminho   = args.get("caminho", "")
        instrucao = args.get("instrucao", "")

        if not caminho:
            return "Qual arquivo, Sir?"
        if not Path(caminho).exists():
            return f"Arquivo nao existe: {caminho}"

        try:
            antigo = Path(caminho).read_text(encoding="utf-8")

            # Backup obrigatorio
            ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
            bkp_dir = Path(caminho).parent / "backups_jarvis"
            bkp_dir.mkdir(exist_ok=True)
            bkp     = bkp_dir / f"{Path(caminho).stem}_{ts}{Path(caminho).suffix}"
            shutil.copy2(caminho, str(bkp))
            print(f"[MODIFICAR] Backup: {bkp.name}")

            # Brain modifica
            prompt = f"""Modifique este codigo Python conforme a instrucao.

INSTRUCAO: {instrucao}

CODIGO ATUAL:
{antigo}

Retorne APENAS o codigo completo modificado. Sem markdown."""

            novo = self.brain.think(prompt, usar_historico=False)
            novo = self._limpar_codigo(novo)

            # Valida AST se for Python
            if caminho.endswith(".py"):
                try:
                    ast.parse(novo)
                except SyntaxError as se:
                    return f"Modificacao quebrou sintaxe: {se}. Backup em {bkp.name}."

            # Diff
            resumo = resumir_diff_voz(antigo, novo)
            diff   = gerar_diff(antigo, novo, Path(caminho).name)
            print(f"\n=== DIFF ===\n{diff}\n=== FIM ===\n")

            Path(caminho).write_text(novo, encoding="utf-8")
            return f"Modifiquei {Path(caminho).name}. {resumo}. Backup: {bkp.name}."

        except Exception as ex:
            return f"Erro: {ex}"

    def _t_rodar_comando(self, args, frase):
        cmd = args.get("comando", "").strip()
        if not cmd:
            return "Qual comando rodar, Sir? Preciso do comando exato."
        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            saida = (r.stdout or r.stderr or "").strip()[:500]
            return f"Resultado: {saida}" if saida else "Executado, Sir."
        except Exception as ex:
            return f"Erro: {ex}"

    def _t_reiniciar_jarvis(self, args, frase):
        """Reinicia o JARVIS via batch."""
        try:
            script = Path(__file__).parent.parent.parent / "main.py"
            self._falar("Reiniciando, Sir. Volto em 30 segundos.")
            bat = Path.home() / "Desktop" / "jarvis_restart.bat"
            bat.write_text(
                f"@echo off\n"
                f"timeout /t 3 /nobreak >nul\n"
                f"cd /d \"{script.parent}\"\n"
                f"call venv\\Scripts\\activate.bat\n"
                f"start \"\" python \"{script}\" --mode hybrid\n"
                f"del \"%~f0\"\n",
                encoding="utf-8",
            )
            subprocess.Popen(["cmd", "/c", str(bat)], shell=True)

            def _kill():
                import time
                time.sleep(2)
                os._exit(0)

            threading.Thread(target=_kill, daemon=True).start()
            return "Reiniciando agora, Sir."
        except Exception as ex:
            return f"Erro ao reiniciar: {ex}"

    # ═══ N5: CRITICO ═══

    def _t_deletar_arquivo(self, args, frase):
        try:
            Path(args.get("caminho", "")).unlink()
            return "Deletado, Sir."
        except Exception as ex:
            return f"Erro: {ex}"

    def _t_deletar_pasta(self, args, frase):
        try:
            shutil.rmtree(args.get("caminho", ""))
            return "Pasta deletada, Sir."
        except Exception as ex:
            return f"Erro: {ex}"

    def _t_instalar_programa(self, args, frase):
        nome = args.get("nome", "")
        try:
            r = subprocess.run(
                f"winget install {nome} -e --silent",
                shell=True, capture_output=True, text=True, timeout=300,
            )
            return "Instalado, Sir." if r.returncode == 0 else f"Falhou: {r.stderr[:200]}"
        except Exception as ex:
            return f"Erro: {ex}"

    def _t_executar_shell(self, args, frase):
        return self._t_rodar_comando(args, frase)

    def _t_executar_ultimo(self, args, frase):
        """Executa o ultimo script criado."""
        if not self._ultimo_arquivo_criado:
            return "Nao tem nenhum script recente, Sir."
        caminho = self._ultimo_arquivo_criado
        if not Path(caminho).exists():
            return f"Arquivo sumiu: {caminho}"
        try:
            r = subprocess.run(
                f'python "{caminho}"',
                shell=True, capture_output=True, text=True, timeout=30,
            )
            saida = (r.stdout or r.stderr or "").strip()[:500]
            nome = Path(caminho).name
            return f"Executei {nome}. Saida: {saida}" if saida else f"Executei {nome}, sem saida."
        except Exception as ex:
            return f"Erro: {ex}"

    # ═══ OUTROS ═══

    def _t_conversar(self, args, frase):
        return args.get("resposta", "Sim, Sir.")

    def _t_perguntar_mais(self, args, frase):
        return args.get("pergunta", "Pode dar mais detalhes, Sir?")


# ═══ SINGLETON ═══
_instance = None

def get_executor(brain=None, dev_agent=None, callback_voz=None, engine=None):
    global _instance
    if _instance is None:
        _instance = ToolExecutor(
            brain=brain,
            dev_agent=dev_agent,
            callback_voz=callback_voz,
            engine=engine,
        )
    return _instance