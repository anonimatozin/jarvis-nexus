"""
NEXUS - App Launcher Inteligente v2.0
Abre apps Windows clássicos E modernos (UWP).
"""

import os
import subprocess
import webbrowser
from typing import Optional


class AppLauncherInteligente:
    """Abre programas com múltiplas estratégias."""

    def __init__(self):
        # Apps clássicos (executáveis)
        self.apps_classicos = {
            "chrome": "chrome.exe",
            "google chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "notepad": "notepad.exe",
            "bloco de notas": "notepad.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "explorador": "explorer.exe",
            "cmd": "cmd.exe",
            "terminal": "wt.exe",
            "powershell": "powershell.exe",
            "vscode": "code.exe",
            "visual studio code": "code.exe",
            "code": "code.exe",
            "discord": "discord.exe",
            "spotify": "spotify.exe",
            "steam": "steam.exe",
            "obs": "obs64.exe",
            "telegram": "telegram.exe",
        }

        # Apps modernos (UWP — URIs)
        self.apps_modernos = {
            "calculadora": "calculator:",
            "calc": "calculator:",
            "calculator": "calculator:",
            "configurações": "ms-settings:",
            "configuracoes": "ms-settings:",
            "settings": "ms-settings:",
            "câmera": "microsoft.windows.camera:",
            "camera": "microsoft.windows.camera:",
            "mapas": "bingmaps:",
            "clima": "msnweather:",
            "loja": "ms-windows-store:",
            "store": "ms-windows-store:",
            "xbox": "xbox:",
            "alarme": "ms-clock:",
            "alarmes": "ms-clock:",
            "relógio": "ms-clock:",
            "fotos": "ms-photos:",
            "filmes": "mswindowsvideo:",
            "spotify uwp": "spotify:",
            "whatsapp": "whatsapp:",
            "outlook": "outlookmail:",
            "mail": "outlookmail:",
            "calendário": "outlookcal:",
            "calendar": "outlookcal:",
        }

        # Compatibilidade com versão antiga
        self.apps = {**self.apps_classicos, **self.apps_modernos}

    def abrir(self, nome: str) -> Optional[bool]:
        """
        Abre aplicativo. Tenta múltiplas estratégias:
        1. App moderno (URI)
        2. App clássico (.exe)
        3. Comando 'start' do Windows
        4. Fallback: tenta como nome de processo
        """
        if not nome:
            return False

        nome = nome.lower().strip()

        # Remove preposições
        for prep in ["o ", "a ", "os ", "as ", "para mim", "pra mim", "por favor"]:
            nome = nome.replace(prep, "").strip()

        # ESTRATÉGIA 1: App moderno (URI)
        for chave, uri in self.apps_modernos.items():
            if chave in nome or nome in chave:
                try:
                    os.startfile(uri)
                    return True
                except Exception as e:
                    print(f"URI {uri} falhou: {e}")

        # ESTRATÉGIA 2: App clássico (.exe)
        for chave, exe in self.apps_classicos.items():
            if chave in nome or nome in chave:
                try:
                    subprocess.Popen(
                        exe,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True
                except Exception:
                    # Tenta com 'start'
                    try:
                        os.system(f"start {exe}")
                        return True
                    except Exception:
                        pass

        # ESTRATÉGIA 3: Calculadora especial (Windows 11)
        if "calc" in nome or "calculadora" in nome:
            try:
                # Método 1: PowerShell direto
                subprocess.Popen(
                    'powershell -Command "Start-Process calc"',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except Exception:
                pass

            try:
                # Método 2: Comando explorer
                subprocess.Popen('explorer.exe shell:AppsFolder\\Microsoft.WindowsCalculator_8wekyb3d8bbwe!App',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except Exception:
                pass

        # ESTRATÉGIA 4: Tenta como comando direto
        try:
            subprocess.Popen(
                f"start {nome}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            pass

        # ESTRATÉGIA 5: Tenta buscar no Windows
        try:
            # Win+S para abrir busca e digitar
            os.system(f"start ms-search:query={nome}")
            return f"Não encontrei '{nome}' direto. Abrindo a busca do Windows."
        except Exception:
            return False