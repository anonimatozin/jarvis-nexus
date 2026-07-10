"""
Gerenciador do pendrive E:\Jarvis - dono total dessa pasta.
Detecta plug/unplug e gerencia sincronia com cache.
"""
import os
import shutil
import time
import threading
from pathlib import Path
from datetime import datetime


# Letra do pendrive (sua escolha)
PENDRIVE_LETTER = "E:"
PENDRIVE_ROOT = Path(PENDRIVE_LETTER) / "Jarvis"

# Cache local (quando pendrive desconectado)
CACHE_ROOT = Path("data/visual_cache")


def pendrive_conectado():
    """Verifica se E: existe e e gravavel."""
    try:
        drive = Path(PENDRIVE_LETTER + "/")
        if not drive.exists():
            return False
        # Tenta criar pasta Jarvis se nao existe
        PENDRIVE_ROOT.mkdir(exist_ok=True)
        # Testa escrita
        test = PENDRIVE_ROOT / ".jarvis_test"
        test.write_text("ok")
        test.unlink()
        return True
    except Exception:
        return False


def get_destino_root():
    """Retorna root onde salvar (pendrive se conectado, cache senao)."""
    if pendrive_conectado():
        return PENDRIVE_ROOT
    return CACHE_ROOT


def get_estrutura_dia(quando=None):
    """Retorna path da pasta do dia/hora."""
    if not quando:
        quando = datetime.now()
    root = get_destino_root()
    return (root / "visual_memory" /
            f"{quando.year}" /
            f"{quando.month:02d}" /
            f"{quando.day:02d}" /
            f"{quando.hour:02d}h")


def get_database_path():
    """Path do banco SQLite (sempre no pendrive se conectado)."""
    root = get_destino_root()
    db_dir = root / "database"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "visual.db"


def get_espaco_livre_mb():
    """Espaco livre no destino atual (em MB)."""
    try:
        root = get_destino_root()
        root.mkdir(parents=True, exist_ok=True)
        stat = shutil.disk_usage(root)
        return stat.free / (1024 * 1024)
    except Exception:
        return 0


def get_espaco_usado_jarvis_mb():
    """Quanto Jarvis ja usou no destino."""
    try:
        root = get_destino_root()
        if not root.exists():
            return 0
        total = 0
        for dp, dn, fn in os.walk(root):
            for f in fn:
                fp = os.path.join(dp, f)
                try:
                    total += os.path.getsize(fp)
                except:
                    pass
        return total / (1024 * 1024)
    except Exception:
        return 0


def listar_cache():
    """Lista arquivos no cache local (pendentes de sincronia)."""
    if not CACHE_ROOT.exists():
        return []
    arquivos = []
    for dp, dn, fn in os.walk(CACHE_ROOT):
        for f in fn:
            arquivos.append(Path(dp) / f)
    return arquivos


def sincronizar_cache_para_pendrive():
    """
    Move tudo do cache local pro pendrive.
    Retorna: numero de arquivos sincronizados.
    """
    if not pendrive_conectado():
        return 0
    if not CACHE_ROOT.exists():
        return 0

    arquivos = listar_cache()
    if not arquivos:
        return 0

    movidos = 0
    for src in arquivos:
        try:
            # Calcula destino: substitui CACHE_ROOT por PENDRIVE_ROOT
            rel = src.relative_to(CACHE_ROOT)
            dst = PENDRIVE_ROOT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            movidos += 1
        except Exception as e:
            print(f"[PENDRIVE] erro move {src}: {e}")

    # Limpa pastas vazias do cache
    try:
        for dp, dn, fn in os.walk(CACHE_ROOT, topdown=False):
            try:
                if not os.listdir(dp):
                    os.rmdir(dp)
            except:
                pass
    except:
        pass

    return movidos


def criar_info_pendrive():
    """Cria arquivo de info no pendrive pra voce ler."""
    if not pendrive_conectado():
        return
    try:
        info = PENDRIVE_ROOT / "LEIA-ME.txt"
        info.write_text(
            "═══════════════════════════════════════════\n"
            "  J.A.R.V.I.S. - MEMORIA VISUAL EXTERNA\n"
            "═══════════════════════════════════════════\n\n"
            "Este pendrive e usado pelo Jarvis para guardar\n"
            "memoria visual do que voce fez no PC.\n\n"
            "AVISOS IMPORTANTES:\n"
            "  - NAO MEXA nos arquivos aqui dentro\n"
            "  - Tudo eh criptografado (AES-256)\n"
            "  - Jarvis gerencia sozinho o que apagar\n"
            "  - Sua chave de descriptografia esta no PC\n"
            "  - Se levar o pendrive em outro PC: nada funciona\n\n"
            "ESTRUTURA:\n"
            "  visual_memory/  - screenshots criptografados\n"
            "  database/       - banco com OCR e metadados\n"
            "  snapshots/      - capturas importantes (nunca apaga)\n"
            "  archive/        - resumos antigos condensados\n\n"
            f"Pendrive iniciado em: {datetime.now()}\n",
            encoding="utf-8"
        )
    except Exception as e:
        print(f"[PENDRIVE] erro info: {e}")
