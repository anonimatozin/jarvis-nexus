"""
NEXUS - Speech Recognition v5.0 - com modo conversa pendente.

Modos:
  - NORMAL: precisa de "Jarvis" no inicio
  - PENDENTE: Jarvis fez uma pergunta, escuta proxima frase sem "Jarvis"
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import speech_recognition as sr
    SR_OK = True
except ImportError:
    SR_OK = False


WAKE_WORDS = [
    "jarvis", "jarves", "jaime", "jarvi", "jervis",
    "service", "darvis", "jervi", "jervice", "carvis",
    "java", "jarves", "jerves"
]

# Timeout do modo pendente (segundos)
PENDENTE_TIMEOUT = 15

# Palavras que normalmente iniciam frase (pos-wake)
_FRASE_INICIO = {
    "qual", "quais", "quanto", "quanta", "quem", "onde", "como",
    "por que", "porque", "pode", "pode me", "me fale", "me diga",
    "abre", "fecha", "liga", "desliga", "ativa", "desativa",
    "mostra", "lista", "procura", "pesquisa", "analisa",
    "que horas", "que dia", "que tempo", "como esta",
    "obrigado", "obrigada", "valeu", "perfeito", "otimo", "show",
}

# Nomes proprios que devem ser capitalizados
_NOMES_PROPRIOS = {
    "jarvis", "discord", "spotify", "chrome", "firefox", "obsidian",
    "vscode", "code", "minecraft", "youtube", "google", "windows",
    "openai", "anthropic", "ollama", "groq", "gemini", "edge",
    "pdf", "csv", "excel", "word", "powerpoint", "github",
    "legiao", "legião", "esp32", "jarvis deck",
}


def _capitalizar_frase(texto):
    """Capitaliza primeira letra de cada frase e nomes proprios."""
    if not texto:
        return texto
    texto = texto.strip()
    # Capitaliza primeira letra
    texto = texto[0].upper() + texto[1:]
    # Capitaliza apos . ! ? ;
    import re
    texto = re.sub(r'([.!?;])\s+([a-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(), texto)
    # Capitaliza nomes proprios (word boundary)
    for nome in _NOMES_PROPRIOS:
        pattern = re.compile(r'\b' + re.escape(nome) + r'\b', re.IGNORECASE)
        texto = pattern.sub(nome.capitalize(), texto)
    return texto


class SpeechEngine:
    def __init__(self):
        self.available = SR_OK
        self.mutado = False
        # NOVO: modo pendente
        self._pendente_ativo = False
        self._pendente_inicio = 0.0

        if not SR_OK:
            print("[STT] speech_recognition nao instalado")
            return

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3500
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 1.2
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.8

        try:
            # Carrega microfone configurado
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
                    print(f"[STT] Microfone configurado: {mic_device_name} (index {device_index})")
                else:
                    self.microphone = sr.Microphone()
                    print(f"[STT] Microfone '{mic_device_name}' nao encontrado, usando padrao")
            else:
                self.microphone = sr.Microphone()
            
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
            mics = sr.Microphone.list_microphone_names()
            print(f"Microfone: {mics[0] if mics else '?'}")
            print("Motor STT v5.0 (wake word + modo pendente).")
        except Exception as e:
            print(f"[STT] Erro mic: {e}")
            self.available = False

    def is_available(self):
        return self.available

    def set_mutado(self, valor: bool):
        self.mutado = bool(valor)
        print(f"[STT] mic {'MUTADO' if self.mutado else 'ATIVO'}")

    def ativar_pendente(self):
        """Ativa modo pendente - proxima frase nao precisa de 'jarvis'."""
        self._pendente_ativo = True
        self._pendente_inicio = time.time()
        print(f"[STT] Modo PENDENTE ativado ({PENDENTE_TIMEOUT}s)")

    def desativar_pendente(self):
        self._pendente_ativo = False

    def _pendente_valido(self):
        if not self._pendente_ativo:
            return False
        if time.time() - self._pendente_inicio > PENDENTE_TIMEOUT:
            self._pendente_ativo = False
            print("[STT] Modo PENDENTE expirou")
            return False
        return True

    def listen_with_wake(self, timeout=5, phrase_time_limit=15):
        """
        Retorna (comando_limpo, frase_original) ou (None, None).
        - Modo NORMAL: precisa de wake word
        - Modo PENDENTE: aceita qualquer frase
        """
        if not self.available or self.mutado:
            return None, None

        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )

            try:
                texto = self.recognizer.recognize_google(audio, language="pt-BR")
                texto = texto.strip()
            except (sr.UnknownValueError, sr.RequestError):
                return None, None

            if not texto:
                return None, None

            tl = texto.lower()
            original = texto

            # MODO PENDENTE: aceita qualquer frase
            if self._pendente_valido():
                texto = _capitalizar_frase(texto)
                print(f"[STT PENDENTE] '{texto[:50]}'")
                # Mesmo em pendente, se tem wake word, remove
                for ww in WAKE_WORDS:
                    if tl.startswith(ww + " ") or tl.startswith(ww + ","):
                        texto = texto[len(ww):].strip(" ,.")
                        break
                self.desativar_pendente()  # consome o pendente
                return texto, original

            # MODO NORMAL: precisa de wake word
            achou_wake = False
            comando_limpo = None

            for ww in WAKE_WORDS:
                if (tl.startswith(ww + " ") or
                    tl.startswith(ww + ",") or
                    tl.startswith(ww + ".") or
                    tl == ww):
                    sem_wake = texto[len(ww):].strip(" ,.!?")
                    comando_limpo = sem_wake
                    achou_wake = True
                    break

            if not achou_wake:
                print(f"[STT IGNORA] '{texto[:50]}'")
                return None, None

            if not comando_limpo:
                print(f"[STT WAKE] (so saudacao)")
                return "", original

            # Capitalizar apos remover wake word
            comando_limpo = _capitalizar_frase(comando_limpo)

            # Filtros anti-falso-positivo
            suspeitos = [
                "no entanto", "infelizmente nao encontrei",
                "minhas pesquisas", "pergunte-me qualquer",
            ]
            tl_cmd = comando_limpo.lower()
            for s in suspeitos:
                if s in tl_cmd:
                    print(f"[STT FILTRO] '{comando_limpo[:50]}'")
                    return None, None

            print(f"[STT CMD] '{comando_limpo}'")
            return comando_limpo, original

        except sr.WaitTimeoutError:
            return None, None
        except Exception as e:
            print(f"[STT] Erro: {e}")
            return None, None

    def listen(self, timeout=4, phrase_time_limit=15):
        cmd, _ = self.listen_with_wake(timeout, phrase_time_limit)
        return cmd

    def listen_command(self, timeout=5, phrase_time_limit=15):
        cmd, _ = self.listen_with_wake(timeout, phrase_time_limit)
        return cmd

    def listen_wake_word(self, timeout=3):
        return False
