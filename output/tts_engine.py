"""
TTS Engine v5.0 - edge-tts (primario) + Kokoro (fallback offline).
Voz principal: edge-tts AntonioNeural (PT-BR masculino, neural).
"""
import os
import asyncio
import tempfile
import threading
import time
from pathlib import Path

import soundfile as sf
import numpy as np
import pygame
from dotenv import load_dotenv

load_dotenv()

# Flag global: True enquanto Jarvis fala
_jarvis_falando = False

# ═══ KOKORO (fallback offline) ═══
_KOKORO_OK = False

try:
    from kokoro_onnx import Kokoro as _Kokoro
    _MODELO_DIR = Path(__file__).resolve().parent.parent
    _MODEL_PATH = _MODELO_DIR / "kokoro-v1.0.onnx"
    _VOICES_PATH = _MODELO_DIR / "voices-v1.0.bin"

    if _MODEL_PATH.exists() and _VOICES_PATH.exists():
        _KOKORO_OK = True
        print("[TTS] Kokoro disponivel (fallback offline)")
except ImportError:
    pass


def _pegar_device_oficial():
    """Pega o device oficial salvo (criptografado) e verifica se existe."""
    try:
        from audio.output_manager import get_oficial
        nome = get_oficial()
        if not nome:
            return None
        
        # Verifica se o device existe
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            for d in devices:
                if nome.lower() in d["name"].lower():
                    return nome
            print(f"[TTS] device oficial '{nome}' nao encontrado, usando padrao")
            return None
        except Exception:
            return nome
    except Exception:
        return None


class TTSEngine:
    """TTS com edge-tts (primario, neural) e Kokoro (fallback offline)."""

    def __init__(self, voz=None):
        self.voz = voz or os.getenv("TTS_VOICE", "pt-BR-AntonioNeural")
        self._edge_rate = os.getenv("TTS_RATE", "-8%")
        self._edge_pitch = os.getenv("TTS_PITCH", "-2Hz")
        self.device_oficial = _pegar_device_oficial()
        self._lock = threading.Lock()
        self._init_pygame_oficial()

        # Kokoro (fallback offline)
        self._kokoro = None
        self._kokoro_voz = os.getenv("KOKORO_VOICE", "pm_alex")
        self._kokoro_lang = os.getenv("KOKORO_LANG", "pt-br")
        self._kokoro_speed = float(os.getenv("KOKORO_SPEED", "1.0"))

        if _KOKORO_OK:
            try:
                self._kokoro = _Kokoro(str(_MODEL_PATH), str(_VOICES_PATH))
            except Exception:
                pass

        print(f"TTS v5.0 | {self.voz} rate={self._edge_rate} pitch={self._edge_pitch}")
        if self._kokoro:
            print(f"  + Kokoro fallback: {self._kokoro_voz}")

    def _init_pygame_oficial(self):
        """Init pygame mixer no device oficial (se houver)."""
        try:
            try:
                pygame.mixer.quit()
            except Exception:
                pass

            if self.device_oficial:
                # Verifica se o device existe antes de tentar usar
                try:
                    import sounddevice as sd
                    devices = sd.query_devices()
                    device_exists = False
                    for d in devices:
                        if self.device_oficial.lower() in d["name"].lower():
                            device_exists = True
                            break
                    
                    if not device_exists:
                        print(f"[TTS] device oficial '{self.device_oficial}' nao encontrado, usando padrao")
                        self.device_oficial = None
                    else:
                        pygame.mixer.pre_init(devicename=self.device_oficial)
                        pygame.mixer.init()
                        return
                except Exception as e:
                    print(f"[TTS] device oficial '{self.device_oficial}' falhou: {e}")

            pygame.mixer.init()
        except Exception as e:
            print(f"[TTS] erro pygame init: {e}")

    def _gerar_kokoro(self, texto, arquivo_wav):
        """Gera audio via Kokoro (local, offline)."""
        try:
            audio, sample_rate = self._kokoro.create(
                texto,
                voice=self._kokoro_voz,
                speed=self._kokoro_speed,
                lang=self._kokoro_lang
            )
            # Garante mono
            if len(audio.shape) == 2:
                audio = np.mean(audio, axis=1)
            # Converte float32 pra int16
            if audio.dtype == np.float32 or audio.dtype == np.float64:
                audio = (audio * 32767).astype(np.int16)
            sf.write(arquivo_wav, audio, sample_rate, subtype='PCM_16')
            return True
        except Exception as e:
            print(f"[TTS] Kokoro erro: {e}")
            return False

    def _gerar_edge(self, texto, arquivo_mp3):
        """Gera audio via edge-tts (online, primario)."""
        import edge_tts

        async def _gen():
            try:
                comm = edge_tts.Communicate(
                    text=texto,
                    voice=self.voz,
                    rate=self._edge_rate,
                    pitch=self._edge_pitch
                )
                await comm.save(arquivo_mp3)
            except Exception:
                comm = edge_tts.Communicate(text=texto, voice="pt-BR-AntonioNeural")
                await comm.save(arquivo_mp3)

        def _run():
            new_loop = asyncio.new_event_loop()
            try:
                new_loop.run_until_complete(_gen())
            finally:
                new_loop.close()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=30)
        return os.path.exists(arquivo_mp3)

    def _tocar_wav(self, arquivo):
        """Toca arquivo WAV de forma segura."""
        try:
            # Metodo 1: pygame.mixer.Sound (mais compativel)
            sound = pygame.mixer.Sound(arquivo)
            canal = sound.play()
            # Espera terminar
            while canal.get_busy():
                time.sleep(0.05)
        except Exception as e1:
            print(f"[TTS] metodo 1 falhou: {e1}")
            try:
                # Metodo 2: converte pra pygame via sndarray
                data, sr = sf.read(arquivo, dtype='int16')
                if len(data.shape) == 2:
                    data = data[:, 0]  # pega so canal esquerdo
                # Garante que e C-contiguous
                data = np.ascontiguousarray(data)
                sound = pygame.sndarray.make_sound(data)
                canal = sound.play()
                while canal.get_busy():
                    time.sleep(0.05)
            except Exception as e2:
                print(f"[TTS] metodo 2 falhou: {e2}")
                # Metodo 3: toca via music (aceita wav)
                try:
                    pygame.mixer.music.load(arquivo)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.05)
                    pygame.mixer.music.unload()
                except Exception as e3:
                    print(f"[TTS] metodo 3 falhou: {e3}")

    def speak(self, texto):
        """Fala texto via TTS. edge-tts primeiro (melhor qualidade), Kokoro fallback."""
        global _jarvis_falando
        _jarvis_falando = True

        if not texto:
            return

        with self._lock:
            tmp = tempfile.NamedTemporaryFile(
                suffix=".mp3", delete=False, prefix="jarvis_tts_"
            )
            arquivo_mp3 = tmp.name
            tmp.close()

            try:
                # 1. Kokoro (primario - offline, confiavel)
                gerado = False
                if self._kokoro:
                    wav = arquivo_mp3.replace(".mp3", ".wav")
                    if self._gerar_kokoro(texto, wav):
                        self._tocar_wav(wav)
                        gerado = True
                    if os.path.exists(wav):
                        try:
                            os.unlink(wav)
                        except Exception:
                            pass

                # 2. edge-tts (fallback online)
                if not gerado:
                    gerado = self._gerar_edge(texto, arquivo_mp3)
                    if gerado and os.path.exists(arquivo_mp3):
                        try:
                            pygame.mixer.music.load(arquivo_mp3)
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.05)
                            pygame.mixer.music.unload()
                        except Exception as e:
                            print(f"[TTS] edge play erro: {e}")
                            gerado = False

            except Exception as e:
                print(f"[TTS] erro speak: {e}")
            finally:
                if os.path.exists(arquivo_mp3):
                    try:
                        os.unlink(arquivo_mp3)
                    except Exception:
                        pass
                import output.tts_engine as _tts_mod
                _tts_mod._jarvis_falando = False

    def parar(self):
        """Interrompe fala atual."""
        try:
            pygame.mixer.music.stop()
            # Para canais de Sound tambem
            for i in range(pygame.mixer.get_num_channels()):
                canal = pygame.mixer.Channel(i)
                canal.stop()
        except Exception:
            pass

    def tocar_musica(self, arquivo_mp3):
        """Toca musica no device padrao."""
        try:
            try:
                pygame.mixer.quit()
            except Exception:
                pass
            pygame.mixer.init()
            pygame.mixer.music.load(arquivo_mp3)
            pygame.mixer.music.play()
            time.sleep(0.5)
            self._init_pygame_oficial()
        except Exception as e:
            print(f"[TTS] erro musica: {e}")

    def listar_vozes(self):
        """Lista vozes disponiveis."""
        vozes = []
        if self._kokoro:
            try:
                vozes_k = self._kokoro.get_voices()
                vozes = [f"[Kokoro] {v}" for v in vozes_k if v.startswith("pf_") or v.startswith("pm_")]
            except Exception:
                pass
        vozes.append(f"[edge-tts] {self.voz}")
        return vozes

    def cleanup(self):
        try:
            pygame.mixer.quit()
        except Exception:
            pass

    def recarregar_device(self):
        """Recarrega o device oficial."""
        self.device_oficial = _pegar_device_oficial()
        self._init_pygame_oficial()
