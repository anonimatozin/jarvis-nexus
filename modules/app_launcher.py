# modules/app_launcher.py
"""
J.A.R.V.I.S. - Módulo de Lançamento de Aplicativos
Abre programas instalados no Windows por nome natural.
"""

import subprocess
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.logger import setup_logger

logger = setup_logger("app_launcher")


class AppLauncher:
    """Gerencia o lançamento de aplicativos no Windows."""
    
    # Mapeamento de nomes naturais para executáveis/comandos
    APP_MAP = {
        # Navegadores
        "chrome": "chrome",
        "google chrome": "chrome",
        "navegador": "chrome",
        "firefox": "firefox",
        "edge": "msedge",
        "microsoft edge": "msedge",
        
        # Ferramentas do sistema
        "notepad": "notepad",
        "bloco de notas": "notepad",
        "calculadora": "calc",
        "calculator": "calc",
        "terminal": "wt",              # Windows Terminal
        "cmd": "cmd",
        "powershell": "powershell",
        "explorador": "explorer",
        "explorador de arquivos": "explorer",
        "gerenciador de tarefas": "taskmgr",
        "task manager": "taskmgr",
        "configurações": "ms-settings:",
        "painel de controle": "control",
        
        # Microsoft Office
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
        "outlook": "outlook",
        
        # Desenvolvimento
        "vscode": "code",
        "visual studio code": "code",
        "visual studio": "devenv",
        
        # Mídia
        "spotify": "spotify",
        "vlc": "vlc",
        
        # Comunicação
        "discord": "discord",
        "teams": "teams",
        "whatsapp": "whatsapp",
        "telegram": "telegram",
    }
    
    @classmethod
    def launch(cls, app_name: str) -> bool:
        """
        Abre um aplicativo pelo nome natural.
        
        Args:
            app_name: Nome do aplicativo (pode ser nome natural)
            
        Returns:
            True se o app foi aberto com sucesso
        """
        app_name_lower = app_name.lower().strip()
        
        # Procura no mapeamento
        executable = cls.APP_MAP.get(app_name_lower)
        
        if executable:
            return cls._execute(executable, app_name)
        
        # Se não encontrou no mapa, tenta abrir diretamente
        return cls._execute(app_name_lower, app_name)
    
    @staticmethod
    def _execute(executable: str, display_name: str) -> bool:
        """
        Executa o programa.
        
        Args:
            executable: Comando ou caminho do executável
            display_name: Nome para exibição no log
            
        Returns:
            True se executado com sucesso
        """
        try:
            # Tenta com os.startfile primeiro (Windows)
            if sys.platform == "win32":
                # Para URLs de configuração do Windows (ms-settings:)
                if executable.startswith("ms-"):
                    os.startfile(executable)
                    logger.info(f"Aplicativo aberto: {display_name}")
                    return True
                
                # Para executáveis normais
                subprocess.Popen(
                    executable,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info(f"Aplicativo aberto: {display_name} ({executable})")
                return True
        
        except FileNotFoundError:
            logger.warning(f"Aplicativo não encontrado: {display_name}")
            return False
        except Exception as e:
            logger.error(f"Erro ao abrir {display_name}: {e}")
            return False
    
    @classmethod
    def launch_url(cls, url: str) -> bool:
        """
        Abre uma URL no navegador padrão.
        
        Args:
            url: URL para abrir
            
        Returns:
            True se aberto com sucesso
        """
        try:
            import webbrowser
            webbrowser.open(url)
            logger.info(f"URL aberta: {url}")
            return True
        except Exception as e:
            logger.error(f"Erro ao abrir URL: {e}")
            return False
    
    @classmethod
    def search_google(cls, query: str) -> bool:
        """
        Faz uma pesquisa no Google.
        
        Args:
            query: Termo de pesquisa
        """
        import urllib.parse
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        return cls.launch_url(url)
    
    @classmethod
    def search_youtube(cls, query: str) -> bool:
        """
        Pesquisa no YouTube.
        
        Args:
            query: Termo de pesquisa
        """
        import urllib.parse
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        return cls.launch_url(url)
    
    @classmethod
    def get_available_apps(cls) -> list:
        """Retorna lista de apps disponíveis no mapeamento."""
        return sorted(cls.APP_MAP.keys())


# === Teste rápido ===
if __name__ == "__main__":
    print("Apps disponíveis:")
    for app in AppLauncher.get_available_apps():
        print(f"  - {app}")
    
    # Teste: abrir calculadora
    # AppLauncher.launch("calculadora")