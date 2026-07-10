"""
JARVIS Hybrid Voice v1.0
Sistema de voz híbrido online/offline para português brasileiro.

Cadeia de fallback:
  TTS: edge-tts (online) → Kokoro (offline) → pyttsx3 (offline nativo)
  STT: Google (online) → Vosk (offline) → pyttsx3 (offline nativo)

Detecta conectivity automaticamente e alterna entre engines.
"""
import os
import sys
import json
import time
import wave
import struct
import tempfile
import threading
import asyncio
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np

# ═══ DETECÇÃO DE CONECTIVIDADE ═══
_conexao_cache = {"online": None, "ultimo_check": 0}
_LOCK = threading.Lock()

def esta_online(timeout: float = 3.0) -> bool:
    """Detecta se há internet. Cache de 10 segundos."""
    import socket
    now = time.time()
    with _LOCK:
        if _conexao_cache["online"] is not None and (now - _conexao_cache["ultimo_check"]) < 10:
            return _conexao_cache["online"]
    try:
        sock = socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        sock.close()
        online = True
    except (OSError, socket.timeout):
        online = False
    with _LOCK:
        _conexao_cache["online"] = online
        _conexao_cache["ultimo_check"] = now
    return online


# ═══ TTS: PYTTSX3 (FALLBACK OFFLINE NATIVO) ═══
_pyttsx3_ok = False
try:
    import pyttsx3 as _pyttsx3
    _pyttsx3_ok = True
except ImportError:
    pass


class Pyttsx3TTS:
    """TTS offline nativo via pyttsx3 (SAPI5 no Windows)."""

    def __init__(self):
        self._engine = None
        self._lock = threading.Lock()
        if _pyttsx3_ok:
            try:
                self._engine = _pyttsx3.init()
                # Tenta voz pt-BR
                for v in self._engine.getProperty("voices"):
                    if "pt" in v.id.lower() or "brazil" in v.name.lower():
                        self._engine.setProperty("voice", v.id)
                        break
                self._engine.setProperty("rate", 150)
                self._engine.setProperty("volume", 0.9)
                print("[TTS] pyttsx3 disponível (offline nativo)")
            except Exception as e:
                print(f"[TTS] pyttsx3 init falhou: {e}")
                self._engine = None

    def speak(self, texto: str) -> bool:
        if not self._engine or not texto:
            return False
        with self._lock:
            try:
                self._engine.say(texto)
                self._engine.runAndWait()
                return True
            except Exception as e:
                print(f"[TTS] pyttsx3 erro: {e}")
                return False

    def available(self) -> bool:
        return self._engine is not None


# ═══ STT: VOSK (OFFLINE) ═══
_vosk_ok = False
_vosk_model = None
_vosk_lock = threading.Lock()

try:
    from vosk import Model as _VoskModel, KaldiRecognizer as _KaldiRecognizer
    _vosk_ok = True
except ImportError:
    pass


def _carregar_vosk():
    """Carrega modelo Vosk PT-BR (lazy)."""
    global _vosk_model
    if _vosk_model is not None:
        return _vosk_model
    if not _vosk_ok:
        return None

    model_dir = Path(__file__).resolve().parent.parent.parent / "models" / "vosk" / "vosk-model-small-pt-0.3"
    if not model_dir.exists():
        print(f"[STT] Modelo Vosk nao encontrado: {model_dir}")
        return None

    try:
        _vosk_model = _VoskModel(str(model_dir))
        print(f"[STT] Modelo Vosk PT-BR carregado: {model_dir.name}")
        return _vosk_model
    except Exception as e:
        print(f"[STT] Erro carregando Vosk: {e}")
        return None


class VoskSTT:
    """STT offline via Vosk com suporte a português."""

    def __init__(self):
        self._model = None
        self._available = False
        if _vosk_ok:
            self._model = _carregar_vosk()
            self._available = self._model is not None

    def recognize(self, audio_data: bytes, sample_rate: int = 16000) -> Optional[str]:
        """Reconhece fala de áudio raw (int16 PCM)."""
        if not self._available or not self._model:
            return None
        with _vosk_lock:
            try:
                rec = _KaldiRecognizer(self._model, sample_rate)
                rec.SetWords(True)
                # Alimenta dados em chunks
                chunk_size = 4000
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    rec.AcceptWaveform(chunk)
                result = json.loads(rec.FinalResult())
                texto = result.get("text", "").strip()
                return texto if texto else None
            except Exception as e:
                print(f"[STT] Vosk erro: {e}")
                return None

    def recognize_file(self, filepath: str) -> Optional[str]:
        """Reconhece fala de arquivo WAV."""
        if not self._available or not self._model:
            return None
        try:
            wf = wave.open(filepath, "rb")
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                print("[STT] Vosk aceita apenas WAV mono 16bit 16kHz")
                return None
            audio_data = wf.readframes(wf.getnframes())
            wf.close()
            return self.recognize(audio_data, wf.getframerate())
        except Exception as e:
            print(f"[STT] Vosk file erro: {e}")
            return None

    def available(self) -> bool:
        return self._available


# ═══ STT: PYAUDIO + VOSK (STREAMING) ═══
_pyaudio_ok = False
try:
    import pyaudio as _pyaudio
    _pyaudio_ok = True
except ImportError:
    pass


class VoskStreamingSTT:
    """STT offline streaming com Vosk + PyAudio."""

    def __init__(self, sample_rate: int = 16000):
        self._sample_rate = sample_rate
        self._model = None
        self._pa = None
        self._stream = None
        self._available = False

        if _pyaudio_ok and _vosk_ok:
            self._model = _carregar_vosk()
            if self._model:
                try:
                    self._pa = _pyaudio.PyAudio()
                    self._available = True
                    print("[STT] Vosk streaming disponível")
                except Exception:
                    pass

    def start_stream(self, callback=None):
        """Inicia streaming do microfone."""
        if not self._available:
            return False
        try:
            # Carrega microfone configurado
            from hud_qt import config as cfg
            mic_device_name = cfg.get("mic_device", "default")
            
            device_index = None
            if mic_device_name and mic_device_name != "default":
                # Encontra o index do microfone pelo nome
                for i in range(self._pa.get_device_count()):
                    dev_info = self._pa.get_device_info_by_index(i)
                    if mic_device_name.lower() in dev_info["name"].lower():
                        device_index = i
                        break
            
            self._stream = self._pa.open(
                format=_pyaudio.paInt16,
                channels=1,
                rate=self._sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=4000
            )
            if device_index is not None:
                print(f"[STT] Vosk stream: {mic_device_name} (index {device_index})")
            return True
        except Exception as e:
            print(f"[STT] Stream erro: {e}")
            return False

    def listen_stream(self, timeout: float = 5.0) -> Optional[str]:
        """Escuta por timeout segundos e retorna texto."""
        if not self._available or not self._stream:
            return None
        try:
            from vosk import KaldiRecognizer as _KR
            rec = _KR(self._model, self._sample_rate)
            start = time.time()
            while (time.time() - start) < timeout:
                data = self._stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    texto = result.get("text", "").strip()
                    if texto:
                        return texto
            result = json.loads(rec.FinalResult())
            texto = result.get("text", "").strip()
            return texto if texto else None
        except Exception as e:
            print(f"[STT] Listen stream erro: {e}")
            return None

    def stop_stream(self):
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def available(self) -> bool:
        return self._available


# ═══ CLASSE PRINCIPAL: HYBRID VOICE ═══
class HybridVoice:
    """
    Sistema de voz híbrido online/offline.
    Auto-detecta conectivity e usa a melhor engine disponível.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}

        # Engines TTS
        self._edge_tts = None
        self._kokoro_tts = None
        self._pyttsx3_tts = Pyttsx3TTS()

        # Engines STT
        self._google_stt = None
        self._vosk_stt = VoskSTT()
        self._vosk_stream = VoskStreamingSTT()

        # Estado
        self._tts_ativo = "auto"  # auto, edge, kokoro, pyttsx3
        self._stt_ativo = "auto"  # auto, google, vosk
        self._falando = False
        self._lock = threading.Lock()

        # Inicializa edge-tts
        try:
            import edge_tts
            self._edge_tts_available = True
        except ImportError:
            self._edge_tts_available = False

        # Inicializa Kokoro
        try:
            from kokoro_onnx import Kokoro as _Kokoro
            model_dir = Path(__file__).resolve().parent.parent.parent
            model_path = model_dir / "kokoro-v1.0.onnx"
            voices_path = model_dir / "voices-v1.0.bin"
            if model_path.exists() and voices_path.exists():
                self._kokoro_tts = _Kokoro(str(model_path), str(voices_path))
                print("[TTS] Kokoro disponível")
        except Exception:
            pass

        # Inicializa speech_recognition para Google
        try:
            import speech_recognition as sr
            self._sr = sr
            self._google_stt = sr.Recognizer()
            self._google_stt.energy_threshold = 3500
            self._google_stt.dynamic_energy_threshold = True
            self._google_stt.pause_threshold = 1.2
            print("[STT] Google Speech disponível")
        except ImportError:
            self._sr = None
            self._google_stt = None

        self._print_status()

    def _print_status(self):
        """Imprime status das engines."""
        status_tts = []
        if self._edge_tts_available:
            status_tts.append("edge-tts(online)")
        if self._kokoro_tts:
            status_tts.append("kokoro(offline)")
        if self._pyttsx3_tts.available():
            status_tts.append("pyttsx3(offline)")

        status_stt = []
        if self._google_stt:
            status_stt.append("google(online)")
        if self._vosk_stt.available():
            status_stt.append("vosk(offline)")

        online = esta_online()
        print(f"\n{'='*50}")
        print(f"  HYBRID VOICE v1.0 | {'ONLINE' if online else 'OFFLINE'}")
        print(f"  TTS: {' > '.join(status_tts) or 'nenhum'}")
        print(f"  STT: {' > '.join(status_stt) or 'nenhum'}")
        print(f"{'='*50}\n")

    # ═══ TTS METHODS ═══

    def falar(self, texto: str, engine: str = "auto") -> bool:
        """
        Fala o texto. Cadeia de fallback automática.
        Returns True se falou com sucesso.
        """
        if not texto or not texto.strip():
            return False

        with self._lock:
            self._falando = True

        try:
            if engine == "auto":
                return self._falar_auto(texto)
            elif engine == "edge":
                return self._falar_edge(texto)
            elif engine == "kokoro":
                return self._falar_kokoro(texto)
            elif engine == "pyttsx3":
                return self._falar_pyttsx3(texto)
        finally:
            with self._lock:
                self._falando = False

    def _falar_auto(self, texto: str) -> bool:
        """Fallback automático: online → offline."""
        online = esta_online()

        # 1. edge-tts (online, melhor qualidade)
        if online and self._edge_tts_available:
            if self._falar_edge(texto):
                return True

        # 2. Kokoro (offline, boa qualidade)
        if self._kokoro_tts:
            if self._falar_kokoro(texto):
                return True

        # 3. pyttsx3 (offline nativo, qualidade básica)
        if self._pyttsx3_tts.available():
            if self._falar_pyttsx3(texto):
                return True

        print("[TTS] Nenhuma engine disponível!")
        return False

    def _falar_edge(self, texto: str) -> bool:
        """Fala via edge-tts (online)."""
        if not self._edge_tts_available:
            return False
        try:
            import edge_tts
            import pygame

            # Inicializa pygame mixer se necessário
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            voz = self.config.get("tts_voice", "pt-BR-AntonioNeural")
            rate = self.config.get("tts_rate", "-8%")
            pitch = self.config.get("tts_pitch", "-2Hz")

            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, prefix="jarvis_")
            arquivo = tmp.name
            tmp.close()

            async def _gen():
                comm = edge_tts.Communicate(text=texto, voice=voz, rate=rate, pitch=pitch)
                await comm.save(arquivo)

            def _run():
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(_gen())
                finally:
                    loop.close()

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            t.join(timeout=30)

            if os.path.exists(arquivo):
                pygame.mixer.music.load(arquivo)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                pygame.mixer.music.unload()
                os.unlink(arquivo)
                return True
        except Exception as e:
            print(f"[TTS] edge-tts erro: {e}")
        return False

    def _falar_kokoro(self, texto: str) -> bool:
        """Fala via Kokoro (offline)."""
        if not self._kokoro_tts:
            return False
        try:
            import soundfile as sf
            import pygame

            # Inicializa pygame mixer se necessário
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            voz = self.config.get("kokoro_voice", "pm_alex")
            lang = self.config.get("kokoro_lang", "pt-br")
            speed = float(self.config.get("kokoro_speed", "1.0"))

            audio, sr = self._kokoro_tts.create(texto, voice=voz, speed=speed, lang=lang)
            if len(audio.shape) == 2:
                audio = np.mean(audio, axis=1)
            if audio.dtype in (np.float32, np.float64):
                audio = (audio * 32767).astype(np.int16)

            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, prefix="jarvis_kokoro_")
            wav_file = tmp.name
            tmp.close()

            sf.write(wav_file, audio, sr, subtype='PCM_16')

            # Toca o WAV
            sound = pygame.mixer.Sound(wav_file)
            canal = sound.play()
            while canal.get_busy():
                time.sleep(0.05)

            os.unlink(wav_file)
            return True
        except Exception as e:
            print(f"[TTS] Kokoro erro: {e}")
        return False

    def _falar_pyttsx3(self, texto: str) -> bool:
        """Fala via pyttsx3 (offline nativo)."""
        return self._pyttsx3_tts.speak(texto)

    def speak(self, texto: str):
        """Compatibilidade com TTSEngine.speak() - chamado pelo engine."""
        self.falar(texto, engine="auto")

    def parar(self):
        """Para a fala atual."""
        try:
            import pygame
            pygame.mixer.music.stop()
            for i in range(pygame.mixer.get_num_channels()):
                pygame.mixer.Channel(i).stop()
        except Exception:
            pass
        with self._lock:
            self._falando = False

    @property
    def falando(self) -> bool:
        return self._falando

    # ═══ STT METHODS ═══

    def escutar(self, timeout: float = 5.0, engine: str = "auto") -> Optional[str]:
        """
        Escuta microfone e retorna texto. Cadeia de fallback automática.
        """
        if engine == "auto":
            return self._escutar_auto(timeout)
        elif engine == "google":
            return self._escutar_google(timeout)
        elif engine == "vosk":
            return self._escutar_vosk(timeout)
        return None

    def _escutar_auto(self, timeout: float) -> Optional[str]:
        """Fallback automático STT."""
        online = esta_online()

        # 1. Google (online, melhor qualidade)
        if online and self._google_stt:
            texto = self._escutar_google(timeout)
            if texto:
                return texto

        # 2. Vosk (offline)
        if self._vosk_stt.available():
            texto = self._escutar_vosk(timeout)
            if texto:
                return texto

        return None

    def _escutar_google(self, timeout: float) -> Optional[str]:
        """STT via Google (online)."""
        if not self._google_stt or not self._sr:
            return None
        try:
            # Carrega microfone configurado
            from hud_qt import config as cfg
            mic_device_name = cfg.get("mic_device", "default")
            
            microphone = None
            if mic_device_name and mic_device_name != "default":
                # Encontra o index do microfone pelo nome
                mics = self._sr.Microphone.list_microphone_names()
                device_index = None
                for i, name in enumerate(mics):
                    if mic_device_name.lower() in name.lower():
                        device_index = i
                        break
                
                if device_index is not None:
                    microphone = self._sr.Microphone(device_index=device_index)
                else:
                    microphone = self._sr.Microphone()
            else:
                microphone = self._sr.Microphone()
            
            with microphone as source:
                self._google_stt.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._google_stt.listen(source, timeout=timeout, phrase_time_limit=15)

            texto = self._google_stt.recognize_google(audio, language="pt-BR")
            return texto.strip() if texto else None
        except self._sr.WaitTimeoutError:
            return None
        except Exception as e:
            print(f"[STT] Google erro: {e}")
            return None

    def _escutar_vosk(self, timeout: float) -> Optional[str]:
        """STT via Vosk (offline)."""
        if not self._vosk_stt.available():
            return None
        try:
            import pyaudio
            
            # Carrega microfone configurado
            from hud_qt import config as cfg
            mic_device_name = cfg.get("mic_device", "default")
            
            pa = pyaudio.PyAudio()
            
            device_index = None
            if mic_device_name and mic_device_name != "default":
                # Encontra o index do microfone pelo nome
                for i in range(pa.get_device_count()):
                    dev_info = pa.get_device_info_by_index(i)
                    if mic_device_name.lower() in dev_info["name"].lower():
                        device_index = i
                        break
            
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=4000
            )

            from vosk import KaldiRecognizer
            rec = KaldiRecognizer(_carregar_vosk(), 16000)

            start = time.time()
            while (time.time() - start) < timeout:
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    texto = result.get("text", "").strip()
                    if texto:
                        stream.stop_stream()
                        stream.close()
                        pa.terminate()
                        return texto

            result = json.loads(rec.FinalResult())
            texto = result.get("text", "").strip()
            stream.stop_stream()
            stream.close()
            pa.terminate()
            return texto if texto else None
        except Exception as e:
            print(f"[STT] Vosk erro: {e}")
            return None

    def escutar_com_wake(self, timeout: float = 5.0, wake_words: list = None) -> Optional[str]:
        """
        Escuta com suporte a wake word.
        Retorna comando limpo (sem wake word) ou None.
        """
        if wake_words is None:
            wake_words = ["jarvis", "jarves", "jarvi"]

        texto = self.escutar(timeout=timeout)
        if not texto:
            return None

        tl = texto.lower().strip()
        for ww in wake_words:
            if tl.startswith(ww + " ") or tl.startswith(ww + ",") or tl.startswith(ww + ".") or tl == ww:
                comando = texto[len(ww):].strip(" ,.!?")
                return comando if comando else ""

        return None

    def listen_with_wake(self, timeout: float = 5.0, phrase_time_limit: float = 15.0) -> Tuple[Optional[str], Optional[str]]:
        """
        Compatível com SpeechEngine.listen_with_wake().
        Retorna (comando_limpo, frase_original) ou (None, None).
        """
        wake_words = ["jarvis", "jarves", "jarvi", "jarvi", "jervis"]
        texto = self.escutar(timeout=timeout)
        if not texto:
            return None, None

        original = texto
        tl = texto.lower().strip()

        # Procura wake word
        for ww in wake_words:
            if tl.startswith(ww + " ") or tl.startswith(ww + ",") or tl.startswith(ww + ".") or tl == ww:
                comando = texto[len(ww):].strip(" ,.!?")
                if comando:
                    return comando, original
                else:
                    return "", original

        # Sem wake word
        return None, None

    def is_available(self) -> bool:
        """Compatível com SpeechEngine.is_available()."""
        return True

    # ═══ INFO METHODS ═══

    def status(self) -> dict:
        """Retorna status das engines."""
        return {
            "online": esta_online(),
            "tts": {
                "edge": self._edge_tts_available,
                "kokoro": self._kokoro_tts is not None,
                "pyttsx3": self._pyttsx3_tts.available(),
            },
            "stt": {
                "google": self._google_stt is not None,
                "vosk": self._vosk_stt.available(),
            },
            "falando": self._falando,
        }

    def listar_vozes(self) -> list:
        """Lista vozes disponíveis."""
        vozes = []
        if self._edge_tts_available:
            vozes.append("edge-tts: pt-BR-AntonioNeural (online)")
        if self._kokoro_tts:
            try:
                vks = self._kokoro_tts.get_voices()
                vozes.extend([f"kokoro: {v}" for v in vks if v.startswith(("pf_", "pm_"))])
            except Exception:
                pass
        if self._pyttsx3_tts.available():
            vozes.append("pyttsx3: voz nativa (offline)")
        return vozes

    def cleanup(self):
        """Libera recursos."""
        self.parar()
        if self._vosk_stream:
            self._vosk_stream.stop_stream()


# ═══ INSTÂNCIA GLOBAL ═══
_instance: Optional[HybridVoice] = None
_instance_lock = threading.Lock()


def get_hybrid_voice(config: dict = None) -> HybridVoice:
    """Retorna instância singleton do HybridVoice."""
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = HybridVoice(config)
        return _instance


def falar(texto: str, engine: str = "auto") -> bool:
    """Função conveniente para falar."""
    return get_hybrid_voice().falar(texto, engine)


def escutar(timeout: float = 5.0, engine: str = "auto") -> Optional[str]:
    """Função conveniente para escutar."""
    return get_hybrid_voice().escutar(timeout, engine)


def parar():
    """Função conveniente para parar fala."""
    get_hybrid_voice().parar()
