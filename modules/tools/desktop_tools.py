# modules/tools/desktop_tools.py
"""
J.A.R.V.I.S. - Desktop Tools Module
31 ferramentas de controle do desktop: mouse, teclado, janelas, midia, clipboard.
Inspirado no PanPenek/JarvisAi.
"""

import os
import subprocess
import time
import json
from pathlib import Path

class DesktopTools:
    """Ferramentas de controle total do desktop."""
    
    def __init__(self):
        self.clipboard_history = []
        self.window_positions = {}
    
    # ═══ MOUSE ═══
    
    def mouse_move(self, x, y):
        """Move o mouse para coordenadas especificas."""
        import pyautogui
        pyautogui.moveTo(x, y, duration=0.3)
        return f"Mouse movido para ({x}, {y})"
    
    def mouse_click(self, x=None, y=None, button='left'):
        """Clica em uma posicao ou na posicao atual."""
        import pyautogui
        if x is not None and y is not None:
            pyautogui.click(x, y, button=button)
            return f"Cliquei em ({x}, {y})"
        else:
            pyautogui.click(button=button)
            return f"Cliquei na posicao atual"
    
    def mouse_double_click(self, x=None, y=None):
        """Duplo clique."""
        import pyautogui
        if x is not None and y is not None:
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.doubleClick()
        return "Duplo clique realizado"
    
    def mouse_right_click(self, x=None, y=None):
        """Clique direito."""
        return self.mouse_click(x, y, button='right')
    
    def mouse_drag(self, x_start, y_start, x_end, y_end, duration=0.5):
        """Arrasta de um ponto para outro."""
        import pyautogui
        pyautogui.moveTo(x_start, y_start)
        pyautogui.drag(x_end - x_start, y_end - y_start, duration=duration)
        return f"Arrastado de ({x_start},{y_start}) para ({x_end},{y_end})"
    
    def mouse_scroll(self, amount):
        """Roda a rola do mouse."""
        import pyautogui
        pyautogui.scroll(amount)
        return f"Rolado {amount} unidades"
    
    # ═══ TECLADO ═══
    
    def type_text(self, text, interval=0.05):
        """Digita um texto."""
        import pyautogui
        pyautogui.typewrite(text, interval=interval)
        return f"Digitado: {text}"
    
    def press_key(self, key):
        """Pressiona uma tecla."""
        import pyautogui
        pyautogui.press(key)
        return f"Tecla '{key}' pressionada"
    
    def hotkey(self, *keys):
        """Combinao de teclas (ex: ctrl+c)."""
        import pyautogui
        pyautogui.hotkey(*keys)
        return f"Combinacao {'+'.join(keys)} executada"
    
    def press_enter(self):
        """Pressiona Enter."""
        return self.press_key('enter')
    
    def press_escape(self):
        """Pressiona Escape."""
        return self.press_key('escape')
    
    def alt_tab(self):
        """Alternar entre janelas."""
        return self.hotkey('alt', 'tab')
    
    def alt_f4(self):
        """Fechar janela atual."""
        return self.hotkey('alt', 'f4')
    
    def ctrl_c(self):
        """Copiar."""
        return self.hotkey('ctrl', 'c')
    
    def ctrl_v(self):
        """Colar."""
        return self.hotkey('ctrl', 'v')
    
    def ctrl_x(self):
        """Recortar."""
        return self.hotkey('ctrl', 'x')
    
    def ctrl_z(self):
        """Desfazer."""
        return self.hotkey('ctrl', 'z')
    
    def ctrl_y(self):
        """Refazer."""
        return self.hotkey('ctrl', 'y')
    
    def ctrl_s(self):
        """Salvar."""
        return self.hotkey('ctrl', 's')
    
    def ctrl_a(self):
        """Selecionar tudo."""
        return self.hotkey('ctrl', 'a')
    
    def win_key(self):
        """Pressiona a tecla Windows."""
        return self.press_key('win')
    
    def print_screen(self):
        """Captura tela."""
        return self.press_key('printscreen')
    
    # ═══ JANELAS ═══
    
    def get_active_window(self):
        """Retorna o titulo da janela ativa."""
        try:
            import pygetwindow as gw
            active = gw.getActiveWindow()
            return active.title if active else "Nenhuma janela ativa"
        except Exception:
            return "Erro ao obter janela ativa"
    
    def list_windows(self):
        """Lista todas as janelas abertas."""
        try:
            import pygetwindow as gw
            windows = gw.getAllWindows()
            return [w.title for w in windows if w.title.strip()]
        except Exception:
            return []
    
    def focus_window(self, title_part):
        """Foca em uma janela pelo titulo."""
        try:
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle(title_part)
            if windows:
                windows[0].activate()
                return f"Focado em: {windows[0].title}"
            return f"Janela '{title_part}' nao encontrada"
        except Exception as e:
            return f"Erro: {e}"
    
    def minimize_window(self):
        """Minimiza a janela ativa."""
        try:
            import pygetwindow as gw
            active = gw.getActiveWindow()
            if active:
                active.minimize()
                return "Janela minimizada"
        except Exception:
            pass
        return "Erro ao minimizar"
    
    def maximize_window(self):
        """Maximiza a janela ativa."""
        try:
            import pygetwindow as gw
            active = gw.getActiveWindow()
            if active:
                active.maximize()
                return "Janela maximizada"
        except Exception:
            pass
        return "Erro ao maximizar"
    
    def close_window(self):
        """Fecha a janela ativa."""
        return self.alt_f4()
    
    # ═══ MIDIA ═══
    
    def media_play_pause(self):
        """Play/Pause midia."""
        return self.press_key('playpause')
    
    def media_next(self):
        """Proxima musica."""
        return self.press_key('nexttrack')
    
    def media_previous(self):
        """Musica anterior."""
        return self.press_key('prevtrack')
    
    def media_stop(self):
        """Para midia."""
        return self.press_key('stop')
    
    def volume_up(self):
        """Aumenta volume."""
        return self.press_key('volumeup')
    
    def volume_down(self):
        """Diminui volume."""
        return self.press_key('volumedown')
    
    def volume_mute(self):
        """Mute/Unmute."""
        return self.press_key('volumemute')
    
    # ═══ CLIPBOARD ═══
    
    def get_clipboard(self):
        """Le o conteudo da area de transferencia."""
        try:
            import subprocess
            result = subprocess.run(['powershell', '-command', 'Get-Clipboard'], 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except Exception:
            return "Erro ao ler clipboard"
    
    def set_clipboard(self, text):
        """Define o conteudo da area de transferencia."""
        try:
            import subprocess
            subprocess.run(['powershell', '-command', f'Set-Clipboard -Value "{text}"'], 
                         capture_output=True)
            self.clipboard_history.append(text)
            return f"Clipboard definido: {text[:50]}..."
        except Exception:
            return "Erro ao definir clipboard"
    
    def clear_clipboard(self):
        """Limpa a area de transferencia."""
        return self.set_clipboard("")
    
    # ═══ SISTEMA ═══
    
    def get_system_info(self):
        """Retorna informacoes do sistema."""
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu,
            'ram_percent': ram.percent,
            'ram_used_gb': round(ram.used / (1024**3), 1),
            'ram_total_gb': round(ram.total / (1024**3), 1),
            'disk_percent': disk.percent,
            'disk_free_gb': round(disk.free / (1024**3), 1)
        }
    
    def kill_process(self, process_name):
        """Mata um processo pelo nome."""
        try:
            subprocess.run(['taskkill', '/f', '/im', process_name], 
                         capture_output=True)
            return f"Processo '{process_name}' finalizado"
        except Exception as e:
            return f"Erro ao finalizar: {e}"
    
    def lock_screen(self):
        """Trava a estacao de trabalho."""
        os.system('rundll32.exe user32.dll,LockWorkStation')
        return "Tela travada"
    
    def open_app(self, app_name):
        """Abre um aplicativo pelo nome."""
        apps = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'explorer': 'explorer.exe',
            'cmd': 'cmd.exe',
            'powershell': 'powershell.exe',
            'task manager': 'taskmgr.exe',
            'paint': 'mspaint.exe',
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'chrome': 'chrome.exe',
            'firefox': 'firefox.exe',
            'vscode': 'code.exe',
        }
        
        app_lower = app_name.lower()
        if app_lower in apps:
            try:
                subprocess.Popen([apps[app_lower]])
                return f"Abrindo {app_name}"
            except Exception as e:
                return f"Erro ao abrir: {e}"
        
        # Tenta abrir diretamente
        try:
            subprocess.Popen([app_name])
            return f"Abrindo {app_name}"
        except Exception as e:
            return f"App '{app_name}' nao encontrado"
    
    def take_screenshot(self, filename=None):
        """Tira uma screenshot."""
        import pyautogui
        if filename is None:
            filename = f"screenshot_{int(time.time())}.png"
        pyautogui.screenshot(filename)
        return f"Screenshot salva: {filename}"
    
    # ═══ PODER ═══
    
    def shutdown(self, seconds=0):
        """Desliga o computador."""
        os.system(f'shutdown /s /t {seconds}')
        return f"Desligando em {seconds} segundos"
    
    def restart(self, seconds=0):
        """Reinicia o computador."""
        os.system(f'shutdown /r /t {seconds}')
        return f"Reiniciando em {seconds} segundos"
    
    def cancel_shutdown(self):
        """Cancela desligamento agendado."""
        os.system('shutdown /a')
        return "Desligamento cancelado"


def criar_comandos_desktop():
    """Retorna dicionario de comandos desktop para o router."""
    tools = DesktopTools()
    
    comandos = {
        # Mouse
        'mover mouse para [x] [y]': lambda texto: tools.mouse_move(*map(int, texto.split()[-2:])),
        'clicar em [x] [y]': lambda texto: tools.mouse_click(*map(int, texto.split()[-2:])),
        'clique duplo': lambda: tools.mouse_double_click(),
        'clique direito': lambda: tools.mouse_right_click(),
        'rolar para cima': lambda: tools.mouse_scroll(3),
        'rolar para baixo': lambda: tools.mouse_scroll(-3),
        
        # Teclado
        'digitar [texto]': lambda texto: tools.type_text(texto.replace('digitar ', '')),
        'enter': lambda: tools.press_enter(),
        'escape': lambda: tools.press_escape(),
        'alt tab': lambda: tools.alt_tab(),
        'copiar': lambda: tools.ctrl_c(),
        'colar': lambda: tools.ctrl_v(),
        'recortar': lambda: tools.ctrl_x(),
        'desfazer': lambda: tools.ctrl_z(),
        'salvar': lambda: tools.ctrl_s(),
        'selecionar tudo': lambda: tools.ctrl_a(),
        
        # Janelas
        'janela ativa': lambda: tools.get_active_window(),
        'listar janelas': lambda: tools.list_windows(),
        'focar [janela]': lambda texto: tools.focus_window(texto.replace('focar ', '')),
        'minimizar': lambda: tools.minimize_window(),
        'maximizar': lambda: tools.maximize_window(),
        'fechar janela': lambda: tools.close_window(),
        
        # Midia
        'play': lambda: tools.media_play_pause(),
        'pause': lambda: tools.media_play_pause(),
        'proxima musica': lambda: tools.media_next(),
        'musica anterior': lambda: tools.media_previous(),
        'volume +': lambda: tools.volume_up(),
        'volume -': lambda: tools.volume_down(),
        'mute': lambda: tools.volume_mute(),
        
        # Sistema
        'info do sistema': lambda: tools.get_system_info(),
        'abrir [app]': lambda texto: tools.open_app(texto.replace('abrir ', '')),
        'fechar [processo]': lambda texto: tools.kill_process(texto.replace('fechar ', '')),
        'tirar screenshot': lambda: tools.take_screenshot(),
        'travar tela': lambda: tools.lock_screen(),
        
        # Poder
        'desligar': lambda: tools.shutdown(),
        'reiniciar': lambda: tools.restart(),
        'cancelar desligamento': lambda: tools.cancel_shutdown(),
    }
    
    return comandos, tools
