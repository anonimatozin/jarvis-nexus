"""
JARVIS File Organizer v1.0
Organização inteligente de arquivos com IA.

Baseado em: michelcrypt4d4mus/clown_sort
Recursos:
  - Organização automática por tipo/conteúdo
  - Renomeação inteligente
  - Limpeza de duplicatas
  - Monitoramento de pastas
  - Categorias automáticas
"""
import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import threading

# ═══ CATEGORIAS DE ARQUIVOS ═══
CATEGORIAS = {
    "documentos": {
        "extensoes": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"],
        "pasta": "Documentos"
    },
    "imagens": {
        "extensoes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"],
        "pasta": "Imagens"
    },
    "videos": {
        "extensoes": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
        "pasta": "Videos"
    },
    "musicas": {
        "extensoes": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
        "pasta": "Musicas"
    },
    "codigos": {
        "extensoes": [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".h", ".php", ".rb", ".go"],
        "pasta": "Codigos"
    },
    "arquivos": {
        "extensoes": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "pasta": "Arquivos"
    },
    "executaveis": {
        "extensoes": [".exe", ".msi", ".dmg", ".app", ".deb", ".rpm"],
        "pasta": "Executaveis"
    },
    "design": {
        "extensoes": [".psd", ".ai", ".sketch", ".fig", ".xd"],
        "pasta": "Design"
    },
    "dados": {
        "extensoes": [".json", ".xml", ".csv", ".sql", ".db", ".sqlite"],
        "pasta": "Dados"
    }
}


class FileOrganizer:
    """Organizador inteligente de arquivos."""

    def __init__(self, pasta_base: str = None):
        self.pasta_base = Path(pasta_base or os.path.expanduser("~\\Downloads"))
        self._historico = []
        self._lock = threading.Lock()
        self._monitorando = False

        print(f"[FILES] Organizador inicializado: {self.pasta_base}")

    def organizar(self, pasta: str = None, mover: bool = True) -> Dict:
        """Organiza arquivos na pasta especificada."""
        pasta = Path(pasta) if pasta else self.pasta_base
        if not pasta.exists():
            print(f"[FILES] Pasta não existe: {pasta}")
            return {"erro": "Pasta não encontrada"}

        estatisticas = {
            "total": 0,
            "organizados": 0,
            "por_categoria": {},
            "erros": []
        }

        for arquivo in pasta.iterdir():
            if arquivo.is_file():
                estatisticas["total"] += 1
                cat = self._obter_categoria(arquivo)

                if cat:
                    pasta_destino = pasta / CATEGORIAS[cat]["pasta"]
                    if mover:
                        try:
                            pasta_destino.mkdir(exist_ok=True)
                            destino = pasta_destino / arquivo.name
                            # Evita sobrescrever
                            if destino.exists():
                                destino = self._gerar_nome_unico(destino)
                            shutil.move(str(arquivo), str(destino))
                            estatisticas["organizados"] += 1
                            estatisticas["por_categoria"][cat] = \
                                estatisticas["por_categoria"].get(cat, 0) + 1

                            self._historico.append({
                                "arquivo": str(arquivo),
                                "destino": str(destino),
                                "categoria": cat,
                                "data": datetime.now().isoformat()
                            })
                        except Exception as e:
                            estatisticas["erros"].append(f"{arquivo.name}: {e}")
                    else:
                        estatisticas["por_categoria"][cat] = \
                            estatisticas["por_categoria"].get(cat, 0) + 1

        print(f"[FILES] Organizados: {estatisticas['organizados']}/{estatisticas['total']}")
        return estatisticas

    def _obter_categoria(self, arquivo: Path) -> Optional[str]:
        """Determina categoria do arquivo."""
        ext = arquivo.suffix.lower()
        for cat, info in CATEGORIAS.items():
            if ext in info["extensoes"]:
                return cat
        return None

    def _gerar_nome_unico(self, path: Path) -> Path:
        """Gera nome único para evitar sobrescrever."""
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        while path.exists():
            path = parent / f"{stem}_{counter}{suffix}"
            counter += 1
        return path

    def renomear_inteligente(self, pasta: str = None, padrao: str = "data_nome") -> int:
        """Renomeia arquivos de forma inteligente."""
        pasta = Path(pasta) if pasta else self.pasta_base
        renomeados = 0

        for arquivo in pasta.iterdir():
            if arquivo.is_file():
                novo_nome = self._gerar_nome(arquivo, padrao)
                if novo_nome and novo_nome != arquivo.name:
                    novo_path = arquivo.parent / novo_nome
                    try:
                        arquivo.rename(novo_path)
                        renomeados += 1
                    except Exception:
                        pass

        print(f"[FILES] {renomeados} arquivos renomeados")
        return renomeados

    def _gerar_nome(self, arquivo: Path, padrao: str) -> Optional[str]:
        """Gera novo nome baseado no padrão."""
        if padrao == "data_nome":
            data = datetime.fromtimestamp(arquivo.stat().st_mtime)
            return f"{data.strftime('%Y%m%d_%H%M%S')}_{arquivo.name}"
        elif padrao == "extensao_nome":
            return f"{arquivo.suffix[1:]}_{arquivo.name}"
        elif padrao == "tamanho_nome":
            tamanho = arquivo.stat().st_size
            return f"{tamanho}_{arquivo.name}"
        return None

    def encontrar_duplicatas(self, pasta: str = None) -> List[List[Path]]:
        """Encontra arquivos duplicados por hash."""
        pasta = Path(pasta) if pasta else self.pasta_base
        hashes = {}
        duplicatas = []

        for arquivo in pasta.rglob("*"):
            if arquivo.is_file():
                try:
                    file_hash = self._calcular_hash(arquivo)
                    if file_hash in hashes:
                        hashes[file_hash].append(arquivo)
                    else:
                        hashes[file_hash] = [arquivo]
                except Exception:
                    pass

        for hash_val, arquivos in hashes.items():
            if len(arquivos) > 1:
                duplicatas.append(arquivos)

        print(f"[FILES] {len(duplicatas)} grupos de duplicatas encontrados")
        return duplicatas

    def _calcular_hash(self, arquivo: Path, chunk_size: int = 8192) -> str:
        """Calcula hash MD5 do arquivo."""
        md5 = hashlib.md5()
        with open(arquivo, "rb") as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()

    def limpar_duplicatas(self, duplicatas: List[List[Path]], manter: str = "maior") -> int:
        """Remove arquivos duplicados."""
        removidos = 0
        for grupo in duplicatas:
            if manter == "maior":
                keeper = max(grupo, key=lambda f: f.stat().st_size)
            elif manter == "mais_antigo":
                keeper = min(grupo, key=lambda f: f.stat().st_mtime)
            else:
                keeper = grupo[0]

            for arquivo in grupo:
                if arquivo != keeper:
                    try:
                        arquivo.unlink()
                        removidos += 1
                    except Exception:
                        pass

        print(f"[FILES] {removidos} duplicatas removidas")
        return removidos

    def obter_tamanho_pasta(self, pasta: str = None) -> Dict:
        """Calcula tamanho da pasta."""
        pasta = Path(pasta) if pasta else self.pasta_base
        total_tamanho = 0
        por_tipo = {}

        for arquivo in pasta.rglob("*"):
            if arquivo.is_file():
                tamanho = arquivo.stat().st_size
                total_tamanho += tamanho
                ext = arquivo.suffix.lower() or "outros"
                por_tipo[ext] = por_tipo.get(ext, 0) + tamanho

        return {
            "total_bytes": total_tamanho,
            "total_mb": round(total_tamanho / (1024 * 1024), 2),
            "por_tipo": por_tipo
        }

    def monitorar_pasta(self, pasta: str = None, intervalo: float = 5.0):
        """Monitora pasta para novos arquivos."""
        pasta = Path(pasta) if pasta else self.pasta_base
        self._monitorando = True
        arquivos_conhecidos = set(f.name for f in pasta.iterdir() if f.is_file())

        def _monitorar():
            while self._monitorando:
                time.sleep(intervalo)
                arquivos_atuais = set(f.name for f in pasta.iterdir() if f.is_file())
                novos = arquivos_atuais - arquivos_conhecidos
                for nome in novos:
                    arquivo = pasta / nome
                    cat = self._obter_categoria(arquivo)
                    print(f"[FILES] Novo arquivo: {nome} ({cat or 'desconhecido'})")
                arquivos_conhecidos.update(arquivos_atuais)

        thread = threading.Thread(target=_monitorar, daemon=True)
        thread.start()
        print(f"[FILES] Monitorando: {pasta}")

    def parar_monitoramento(self):
        """Para monitoramento."""
        self._monitorando = False

    def obter_historico(self) -> List[Dict]:
        """Retorna histórico de organização."""
        with self._lock:
            return self._historico.copy()

    def status(self) -> Dict:
        """Retorna status do organizador."""
        return {
            "pasta_base": str(self.pasta_base),
            "arquivos_organizados": len(self._historico),
            "monitorando": self._monitorando
        }


# ═══ INSTANCIA GLOBAL ═══
_file_instance = None


def get_file_organizer(pasta: str = None) -> FileOrganizer:
    """Retorna instância do File Organizer."""
    global _file_instance
    if _file_instance is None:
        _file_instance = FileOrganizer(pasta)
    return _file_instance
