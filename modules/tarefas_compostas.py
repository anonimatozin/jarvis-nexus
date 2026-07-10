"""
NEXUS - Sistema de Tarefas Compostas v1.0
═══════════════════════════════════════════════════════════
Modos personalizados que executam multiplas acoes em sequencia.
Cada "modo" e uma serie de passos definidos.
═══════════════════════════════════════════════════════════
"""

import os
import time
import subprocess
import webbrowser
from typing import List, Dict, Callable, Optional


class TarefasCompostas:
    """Executor de modos / rotinas personalizadas."""
    
    def __init__(self, app_launcher=None, system_control=None):
        self.app_launcher = app_launcher
        self.system_control = system_control
        self.executando = False
        
        # Define todas as rotinas
        self.rotinas = {
            "trabalho": self._modo_trabalho,
            "estudo": self._modo_trabalho,  # alias
            "preparar pc": self._modo_trabalho,  # alias
            "preparar computador": self._modo_trabalho,  # alias
            
            "minecraft": self._modo_minecraft,
            "mine": self._modo_minecraft,  # alias
            "jogar": self._modo_minecraft,  # alias
            
            "gravacao": self._modo_gravacao,
            "gravar": self._modo_gravacao,  # alias
            "gravando": self._modo_gravacao,  # alias
            "live": self._modo_gravacao,  # alias
            
            "edicao": self._modo_edicao,
            "editar": self._modo_edicao,  # alias
            
            "dormir": self._modo_dormir,
            "boa noite": self._modo_dormir,  # alias
            "desligar tudo": self._modo_dormir,  # alias
            
            "foco": self._modo_foco,
            "focar": self._modo_foco,  # alias
            
            "descansar": self._modo_descansar,
            "relaxar": self._modo_descansar,  # alias
            
            "reset": self._modo_reset,
            "limpar tudo": self._modo_reset,
        }
    
    # ════════════════════════════════════════════════════════
    # API PRINCIPAL
    # ════════════════════════════════════════════════════════
    
    def executar(self, nome_rotina: str) -> str:
        """Executa uma rotina pelo nome."""
        nome = nome_rotina.lower().strip()
        
        # Busca rotina (case-insensitive, match parcial)
        rotina_func = None
        rotina_nome_real = None
        for chave, func in self.rotinas.items():
            if chave in nome or nome in chave:
                rotina_func = func
                rotina_nome_real = chave
                break
        
        if not rotina_func:
            return self.listar_rotinas()
        
        if self.executando:
            return "Ja estou executando uma rotina, aguarde."
        
        try:
            self.executando = True
            print(f"\n[ROTINA] Iniciando: {rotina_nome_real}")
            resultado = rotina_func()
            print(f"[ROTINA] Concluida: {rotina_nome_real}")
            return resultado
        except Exception as e:
            return f"Erro ao executar rotina: {e}"
        finally:
            self.executando = False
    
    def listar_rotinas(self) -> str:
        """Lista todas as rotinas disponiveis."""
        # Pega nomes unicos (sem aliases duplicados)
        nomes_unicos = set()
        for chave, func in self.rotinas.items():
            nomes_unicos.add(func.__name__.replace("_modo_", ""))
        
        return "Modos disponiveis: " + ", ".join(sorted(nomes_unicos))
    
    # ════════════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════════════
    
    def _abrir(self, app: str) -> bool:
        """Abre um app via launcher."""
        if not self.app_launcher:
            return False
        try:
            resultado = self.app_launcher.abrir(app)
            time.sleep(1)  # da tempo do app abrir
            return bool(resultado)
        except Exception as e:
            print(f"  [ERRO] Abrir {app}: {e}")
            return False
    
    def _abrir_url(self, url: str) -> bool:
        """Abre URL no navegador padrao."""
        try:
            webbrowser.open(url)
            time.sleep(0.5)
            return True
        except Exception:
            return False
    
    def _fechar(self, processo: str) -> bool:
        """Fecha processo pelo nome do exe."""
        try:
            subprocess.Popen(
                f"taskkill /f /im {processo}",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False
    
    def _set_volume(self, nivel: int) -> bool:
        """Ajusta volume."""
        if not self.system_control:
            return False
        try:
            self.system_control.set_volume(nivel)
            return True
        except Exception:
            return False
    
    def _bloquear_tela(self) -> bool:
        """Bloqueia a tela do PC."""
        if not self.system_control:
            return False
        try:
            self.system_control.lock_screen()
            return True
        except Exception:
            return False
    
    # ════════════════════════════════════════════════════════
    # ROTINAS PERSONALIZADAS
    # ════════════════════════════════════════════════════════
    
    def _modo_trabalho(self) -> str:
        """Prepara ambiente de trabalho/estudo."""
        acoes = []
        
        if self._abrir("chrome"):
            acoes.append("Chrome aberto")
        
        time.sleep(1)
        
        if self._abrir("vscode"):
            acoes.append("VS Code aberto")
        
        time.sleep(1)
        
        # Abre Arena IA no navegador
        if self._abrir_url("https://arena.ai"):
            acoes.append("Arena IA aberto")
        
        if self._set_volume(30):
            acoes.append("volume em 30%")
        
        if not acoes:
            return "Nao consegui preparar o ambiente."
        
        return f"Ambiente de trabalho pronto, Sir. {', '.join(acoes)}."
    
    def _modo_minecraft(self) -> str:
        """Modo Minecraft - fecha pesados, abre SKLauncher."""
        acoes = []
        
        # Fecha apps que comem RAM
        if self._fechar("chrome.exe"):
            acoes.append("Chrome fechado")
        if self._fechar("Code.exe"):
            acoes.append("VS Code fechado")
        if self._fechar("Discord.exe"):
            acoes.append("Discord fechado")
        
        time.sleep(1)
        
        # Abre SKLauncher
        if self._abrir("sklauncher"):
            acoes.append("SKLauncher aberto")
        else:
            # Tenta caminhos comuns do SKLauncher
            caminhos = [
                os.path.expanduser("~/AppData/Local/SKlauncher/SKlauncher.exe"),
                os.path.expanduser("~/Desktop/SKlauncher.exe"),
                "C:/Program Files/SKlauncher/SKlauncher.exe",
            ]
            for caminho in caminhos:
                if os.path.exists(caminho):
                    subprocess.Popen(caminho, shell=True)
                    acoes.append("SKLauncher aberto")
                    break
        
        if self._set_volume(50):
            acoes.append("volume em 50%")
        
        if not acoes:
            return "Nao consegui preparar pra Minecraft."
        
        return f"Bom jogo, Sir. {', '.join(acoes)}."
    
    def _modo_gravacao(self) -> str:
        """Modo gravacao - SKLauncher + OBS."""
        acoes = []
        
        # Abre SKLauncher
        if self._abrir("sklauncher"):
            acoes.append("SKLauncher aberto")
        else:
            caminhos = [
                os.path.expanduser("~/AppData/Local/SKlauncher/SKlauncher.exe"),
                "C:/Program Files/SKlauncher/SKlauncher.exe",
            ]
            for c in caminhos:
                if os.path.exists(c):
                    subprocess.Popen(c, shell=True)
                    acoes.append("SKLauncher aberto")
                    break
        
        time.sleep(2)
        
        # Abre OBS
        obs_paths = [
            "C:/Program Files/obs-studio/bin/64bit/obs64.exe",
            "C:/Program Files (x86)/obs-studio/bin/64bit/obs64.exe",
        ]
        obs_aberto = False
        for path in obs_paths:
            if os.path.exists(path):
                try:
                    # OBS precisa ser aberto na pasta dele
                    subprocess.Popen(
                        path,
                        cwd=os.path.dirname(path),
                        shell=True,
                    )
                    acoes.append("OBS aberto")
                    obs_aberto = True
                    break
                except Exception as e:
                    print(f"Erro OBS: {e}")
        
        if not obs_aberto:
            if self._abrir("obs"):
                acoes.append("OBS aberto")
        
        if self._set_volume(70):
            acoes.append("volume em 70%")
        
        if not acoes:
            return "Nao consegui preparar pra gravacao."
        
        return f"Tudo pronto pra gravar, Sir. {', '.join(acoes)}."
    
    def _modo_edicao(self) -> str:
        """Modo edicao - CapCut + Audacity."""
        acoes = []
        
        # CapCut
        capcut_paths = [
            os.path.expanduser("~/AppData/Local/CapCut/Apps/CapCut.exe"),
            "C:/Program Files/CapCut/CapCut.exe",
        ]
        capcut_aberto = False
        for path in capcut_paths:
            if os.path.exists(path):
                subprocess.Popen(path, shell=True)
                acoes.append("CapCut aberto")
                capcut_aberto = True
                break
        
        if not capcut_aberto:
            if self._abrir("capcut"):
                acoes.append("CapCut aberto")
            else:
                acoes.append("(CapCut nao encontrado)")
        
        # Audacity
        audacity_paths = [
            "C:/Program Files/Audacity/Audacity.exe",
            "C:/Program Files (x86)/Audacity/Audacity.exe",
        ]
        audacity_aberto = False
        for path in audacity_paths:
            if os.path.exists(path):
                subprocess.Popen(path, shell=True)
                acoes.append("Audacity aberto")
                audacity_aberto = True
                break
        
        if not audacity_aberto:
            if self._abrir("audacity"):
                acoes.append("Audacity aberto")
            else:
                acoes.append("(Audacity nao instalado)")
        
        if not acoes:
            return "Nao consegui preparar pra edicao."
        
        return f"Estudio pronto, Sir. {', '.join(acoes)}."
    
    def _modo_dormir(self) -> str:
        """Modo dormir - fecha tudo + bloqueia tela."""
        acoes = []
        
        # Fecha varios apps comuns
        apps_fechar = [
            ("chrome.exe", "Chrome"),
            ("Code.exe", "VS Code"),
            ("Discord.exe", "Discord"),
            ("Spotify.exe", "Spotify"),
            ("steam.exe", "Steam"),
            ("obs64.exe", "OBS"),
            ("CapCut.exe", "CapCut"),
        ]
        
        for processo, nome in apps_fechar:
            if self._fechar(processo):
                acoes.append(nome)
        
        time.sleep(1)
        
        # Bloqueia tela
        if self._bloquear_tela():
            return f"Boa noite, Sir. Fechei {len(acoes)} programas e bloqueei a tela."
        
        return f"Boa noite, Sir. Fechei {len(acoes)} programas."
    
    def _modo_foco(self) -> str:
        """Modo foco - fecha distracoes, volume baixo."""
        acoes = []
        
        # Fecha distratores
        if self._fechar("Discord.exe"):
            acoes.append("Discord fechado")
        if self._fechar("Spotify.exe"):
            acoes.append("Spotify fechado")
        
        # Volume baixo
        if self._set_volume(20):
            acoes.append("volume em 20%")
        
        return f"Foco total ativado, Sir. {', '.join(acoes)}."
    
    def _modo_descansar(self) -> str:
        """Modo descansar - YouTube relaxante."""
        acoes = []
        
        if self._abrir_url("https://www.youtube.com"):
            acoes.append("YouTube aberto")
        
        if self._set_volume(60):
            acoes.append("volume em 60%")
        
        return f"Hora de relaxar, Sir. {', '.join(acoes)}."
    
    def _modo_reset(self) -> str:
        """Reset - fecha tudo (sem bloquear tela)."""
        apps_fechar = [
            "chrome.exe", "Code.exe", "Discord.exe", "Spotify.exe",
            "steam.exe", "obs64.exe", "CapCut.exe", "Audacity.exe",
        ]
        
        contador = 0
        for proc in apps_fechar:
            if self._fechar(proc):
                contador += 1
        
        return f"Ambiente limpo, Sir. {contador} programas fechados."
