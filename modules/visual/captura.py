"""
Captura screenshot + OCR + criptografia.
"""
import io
import time
import warnings
from datetime import datetime
from pathlib import Path

# Suprime warnings de mss
warnings.filterwarnings("ignore", category=DeprecationWarning, module="mss")
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    import mss
    MSS_OK = True
except ImportError:
    MSS_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import pytesseract
    PYTESSERACT_OK = True
except ImportError:
    PYTESSERACT_OK = False

from cryptography.fernet import Fernet
from security.crypto import _derive_key
from modules.visual.pendrive import get_estrutura_dia


def _get_fernet():
    return Fernet(_derive_key())


def capturar_tela():
    """Captura screenshot da tela primaria. Retorna bytes PNG."""
    if not MSS_OK:
        return None
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            if img.width > 1280:
                ratio = 1280 / img.width
                new_h = int(img.height * ratio)
                img = img.resize((1280, new_h), Image.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue()
    except Exception as e:
        print(f"[CAPTURA] erro screenshot: {e}")
        return None


def rodar_ocr(image_bytes):
    """Roda OCR no screenshot. Retorna texto."""
    if not PYTESSERACT_OK or not PIL_OK:
        return ""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        texto = pytesseract.image_to_string(img, lang="por+eng", config="--oem 3 --psm 6")
        return texto.strip()[:5000]
    except Exception as e:
        print(f"[OCR] erro: {e}")
        return ""


def criptografar_e_salvar(image_bytes, quando=None):
    """Criptografa e salva. Retorna (path, tamanho_kb) ou (None, 0)."""
    if not image_bytes:
        return None, 0

    if not quando:
        quando = datetime.now()

    try:
        f = _get_fernet()
        encrypted = f.encrypt(image_bytes)

        pasta = get_estrutura_dia(quando)
        pasta.mkdir(parents=True, exist_ok=True)

        nome = f"{quando.hour:02d}h{quando.minute:02d}_{quando.second:02d}.enc"
        path = pasta / nome
        path.write_bytes(encrypted)

        tamanho_kb = len(encrypted) / 1024
        return path, tamanho_kb
    except Exception as e:
        print(f"[CAPTURA] erro criptografar/salvar: {e}")
        return None, 0


def descriptografar(path):
    """Descriptografa um screenshot. Retorna bytes PNG ou None."""
    try:
        f = _get_fernet()
        encrypted = Path(path).read_bytes()
        return f.decrypt(encrypted)
    except Exception as e:
        print(f"[CAPTURA] erro decrypt: {e}")
        return None


def get_janela_ativa():
    """Pega titulo + processo da janela ativa (Windows)."""
    try:
        import win32gui
        import win32process
        import psutil

        hwnd = win32gui.GetForegroundWindow()
        titulo = win32gui.GetWindowText(hwnd) or ""
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        app = proc.name() or ""
        return app, titulo
    except Exception:
        return "", ""


def calcular_pontuacao(ocr_texto, app, titulo, dura_tempo=False):
    """Pontuacao 0-100 da importancia."""
    score = 40

    if len(ocr_texto) > 500:
        score += 20
    elif len(ocr_texto) > 100:
        score += 10
    elif len(ocr_texto) < 20:
        score -= 15

    apps_importantes = ["code.exe", "vscode", "chrome", "firefox", "edge",
                        "discord", "notion", "obsidian", "word", "excel",
                        "pycharm", "intellij", "sublime"]
    apps_baixo = ["spotify", "vlc", "netflix", "wmplayer", "potplayer",
                  "steam", "epicgames"]

    app_l = (app or "").lower()
    for ai in apps_importantes:
        if ai in app_l:
            score += 15
            break
    for ab in apps_baixo:
        if ab in app_l:
            score -= 20
            break

    if "lock" in (titulo or "").lower() or "screensaver" in app_l:
        score = 5

    keywords_uteis = ["tutorial", "documentation", "stack", "github",
                       "como ", "how to", "guia", "manual"]
    titulo_l = (titulo or "").lower()
    for k in keywords_uteis:
        if k in titulo_l:
            score += 10
            break

    return max(0, min(100, score))
