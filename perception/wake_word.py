# perception/wake_word.py - VERSÃO CORRIGIDA (SEM PYAUDIO)
"""
Wake Word usando speech_recognition + sounddevice
Sem necessidade de PyAudio
"""

import time
import threading
import speech_recognition as sr

from utils.logger import setup_logger, print_success, print_system

logger = setup_logger("wake_word")

class WakeWordDetector:
    """
    Detector de palavra de ativação usando speech_recognition
    """
    
    def __init__(self, wake_words=["jarvis", "jar vis"], sensitivity=0.5):
        self.wake_words = wake_words
        self.sensitivity = sensitivity
        self.is_listening = False
        self.callback = None
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.listener_thread = None
        
    def start(self, callback=None):
        """Inicia o detector em background"""
        self.callback = callback
        self.is_listening = True
        
        # Inicializa microfone com configuracao
        try:
            from hud_qt import config as cfg
            mic_device_name = cfg.get("mic_device", "default")
            
            if mic_device_name and mic_device_name != "default":
                # Encontra o index do microfone pelo nome
                mics = sr.Microphone.list_microphone_names()
                device_index = None
                for i, name in enumerate(mics):
                    if mic_device_name.lower() in name.lower():
                        device_index = i
                        break
                
                if device_index is not None:
                    self.microphone = sr.Microphone(device_index=device_index)
                    print_system(f"[WAKE] Microfone: {mic_device_name} (index {device_index})")
                else:
                    self.microphone = sr.Microphone()
                    print_system(f"[WAKE] Microfone '{mic_device_name}' nao encontrado, usando padrao")
            else:
                self.microphone = sr.Microphone()
            
            with self.microphone as source:
                print_system("Ajustando para ruido ambiente...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print_success("Wake Word ativo. Diga 'Jarvis' para me ativar.")
        except Exception as e:
            logger.error(f"Microfone não disponível: {e}")
            print_system("Wake Word desativado - microfone não encontrado.")
            return
            
        # Thread de escuta
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        
    def _listen_loop(self):
        """Loop principal de escuta"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    # Escuta com timeout curto para não travar
                    audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=2)
                    
                    # Tenta reconhecer
                    try:
                        text = self.recognizer.recognize_google(audio, language='pt-BR').lower()
                        
                        # Verifica se contém "jarvis"
                        for wake in self.wake_words:
                            if wake in text:
                                logger.info(f"Wake word detectada: '{text}'")
                                if self.callback:
                                    self.callback()
                                break
                                
                    except sr.UnknownValueError:
                        pass  # não entendeu, ignora
                    except sr.RequestError:
                        pass  # erro de rede, ignora
                        
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                logger.debug(f"Erro no wake word: {e}")
                
    def stop(self):
        """Para o detector"""
        self.is_listening = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1)
        print_system("Wake Word desativado.")