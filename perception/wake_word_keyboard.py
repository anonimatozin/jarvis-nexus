# perception/wake_word_keyboard.py
import threading
from pynput import keyboard
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import corrigido - sem o 'logger' que não existe
from utils.logger import print_success, print_system

class WakeWordKeyboard:
    def __init__(self):
        self.is_listening = False
        self.callback = None
        self.listener = None
        
    def start(self, callback=None):
        self.callback = callback
        self.is_listening = True
        
        def on_press(key):
            try:
                if hasattr(key, 'char') and (key.char == 'j' or key.char == 'J'):
                    print_system("🎤 Tecla 'J' pressionada (ativando Jarvis)")
                    if self.callback:
                        self.callback()
            except Exception:
                pass
                
        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.start()
        print_success("Wake Word (teclado) ativo. Pressione 'J' para me ativar.")
        
    def stop(self):
        self.is_listening = False
        if self.listener:
            self.listener.stop()
        print_system("Wake Word (teclado) desativado.")