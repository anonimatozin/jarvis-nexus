"""
Gerencia inicio com Windows via registro do sistema.
"""
import os
import sys
from pathlib import Path

APP_NAME = "JARVIS_NEXUS"
JARVIS_ROOT = Path(__file__).resolve().parent.parent
BAT_FILE = JARVIS_ROOT / "scripts" / "jarvis_start.bat"


def _ensure_bat():
    """Cria o jarvis_start.bat."""
    venv_act = JARVIS_ROOT / "venv" / "Scripts" / "activate.bat"
    main_py = JARVIS_ROOT / "main.py"

    # Usa pythonw pra nao aparecer console (modo silencioso)
    content = f"""@echo off
cd /d "{JARVIS_ROOT}"
call "{venv_act}"
start "" /min pythonw "{main_py}" --mode hybrid
"""
    BAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BAT_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def set_startup(enabled: bool) -> bool:
    """Liga/desliga inicio com Windows."""
    try:
        import winreg
    except ImportError:
        print("[STARTUP] winreg nao disponivel")
        return False

    try:
        key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )

        if enabled:
            _ensure_bat()
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, str(BAT_FILE))
            print(f"[STARTUP] Registrado: {BAT_FILE}")
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
                print("[STARTUP] Removido do boot")
            except FileNotFoundError:
                pass

        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[STARTUP] erro: {e}")
        return False


def is_startup_enabled() -> bool:
    try:
        import winreg
        key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_QUERY_VALUE
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False
