"""
NEXUS - Auto-start no Windows
Adiciona/remove do registro do Windows (HKCU/Run).
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "JarvisNEXUS"


def get_launcher_path():
    """Caminho do launcher .pyw (silencioso)."""
    return str(PROJECT_ROOT / "boot" / "jarvis_bg.pyw")


def get_pythonw():
    """Encontra pythonw.exe (Python sem console)."""
    venv_pyw = PROJECT_ROOT / "venv" / "Scripts" / "pythonw.exe"
    if venv_pyw.exists():
        return str(venv_pyw)
    python_exe = Path(sys.executable)
    pythonw = python_exe.parent / "pythonw.exe"
    if pythonw.exists():
        return str(pythonw)
    return sys.executable


def enable_autostart():
    """Registra o Jarvis para iniciar com o Windows."""
    try:
        import winreg
        pythonw = get_pythonw()
        launcher = get_launcher_path()
        command = f'"{pythonw}" "{launcher}"'

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        print(f"[autostart] habilitado: {command}")
        return True
    except Exception as e:
        print(f"[autostart] erro ao habilitar: {e}")
        return False


def disable_autostart():
    """Remove do auto-start."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        print("[autostart] desabilitado")
        return True
    except Exception as e:
        print(f"[autostart] erro ao desabilitar: {e}")
        return False


def is_autostart_enabled():
    """Verifica se esta registrado."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY, 0, winreg.KEY_READ
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


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["enable", "disable", "status"])
    a = p.parse_args()

    if a.action == "enable":
        ok = enable_autostart()
        print("[OK] Auto-start ATIVADO" if ok else "[ERRO] Falha")
    elif a.action == "disable":
        ok = disable_autostart()
        print("[OK] Auto-start DESATIVADO" if ok else "[ERRO] Falha")
    else:
        print(f"Auto-start: {'ATIVADO' if is_autostart_enabled() else 'DESATIVADO'}")
