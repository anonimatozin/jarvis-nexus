"""
JARVIS Music Generation v1.0
Geração e análise de música com IA.

Baseado em: AIGC-Audio/AudioGPT (10.2k stars)
Recursos:
  - Geração de melodia
  - Análise de áudio
  - Conversão de partitura
  - Efeitos sonoros
  - Visualização de áudio
"""
import os
import json
import math
import struct
import wave
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import threading

# ═══ DEPENDENCIAS ═══
_numpy_ok = False
_soundfile_ok = False
_pygame_ok = False

try:
    import numpy as np
    _numpy_ok = True
except ImportError:
    pass

try:
    import soundfile as sf
    _soundfile_ok = True
except ImportError:
    pass

try:
    import pygame
    _pygame_ok = True
except ImportError:
    pass


# ═══ NOTAS MUSICAIS ═══
NOTAS = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46,
    "G5": 783.99, "A5": 880.00, "B5": 987.77,
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61,
    "G3": 196.00, "A3": 220.00, "B3": 246.94,
}


class MusicGenerator:
    """Gerador de música e análise de áudio."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self._lock = threading.Lock()

        print(f"[MUSIC] Gerador inicializado")
        print(f"  NumPy: {'✅' if _numpy_ok else '❌'}")
        print(f"  SoundFile: {'✅' if _soundfile_ok else '❌'}")
        print(f"  Pygame: {'✅' if _pygame_ok else '❌'}")

    def gerar_nota(self, nota: str, duracao: float = 0.5,
                   volume: float = 0.7) -> Optional[str]:
        """Gera uma nota musical."""
        if not _numpy_ok or not _soundfile_ok:
            print("[MUSIC] NumPy/SoundFile necessário")
            return None

        freq = NOTAS.get(nota.upper())
        if not freq:
            print(f"[MUSIC] Nota inválida: {nota}")
            return None

        t = np.linspace(0, duracao, int(self.sample_rate * duracao), False)
        # Onda sinusoidal com envelope
        onda = np.sin(2 * np.pi * freq * t) * volume
        # Envelope ADSR simples
        attack = int(0.01 * self.sample_rate)
        decay = int(0.05 * self.sample_rate)
        release = int(0.1 * self.sample_rate)
        envelope = np.ones_like(onda)
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[attack:attack+decay] = np.linspace(1, 0.8, decay)
        envelope[-release:] = np.linspace(0.8, 0, release)
        onda *= envelope

        # Salva
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, prefix="nota_")
        arquivo = tmp.name
        tmp.close()

        sf.write(arquivo, onda, self.sample_rate, subtype='PCM_16')
        return arquivo

    def gerar_melodia(self, notas: List[Tuple[str, float]],
                      volume: float = 0.7) -> Optional[str]:
        """Gera melodia a partir de lista de (nota, duracao)."""
        if not _numpy_ok or not _soundfile_ok:
            return None

        audio_completo = np.array([])

        for nota, duracao in notas:
            freq = NOTAS.get(nota.upper(), 0)
            if freq == 0:
                # Silêncio
                silencio = np.zeros(int(self.sample_rate * duracao))
                audio_completo = np.concatenate([audio_completo, silencio])
                continue

            t = np.linspace(0, duracao, int(self.sample_rate * duracao), False)
            onda = np.sin(2 * np.pi * freq * t) * volume

            # Envelope
            attack = int(0.01 * self.sample_rate)
            release = int(0.05 * self.sample_rate)
            envelope = np.ones_like(onda)
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-release:] = np.linspace(1, 0, release)
            onda *= envelope

            audio_completo = np.concatenate([audio_completo, onda])

        # Salva
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, prefix="melodia_")
        arquivo = tmp.name
        tmp.close()

        sf.write(arquivo, audio_completo, self.sample_rate, subtype='PCM_16')
        print(f"[MUSIC] Melodia gerada: {len(notas)} notas")
        return arquivo

    def gerar_acorde(self, notas: List[str], duracao: float = 1.0,
                     volume: float = 0.5) -> Optional[str]:
        """Gera acorde (múltiplas notas simultâneas)."""
        if not _numpy_ok or not _soundfile_ok:
            return None

        audio_total = np.zeros(int(self.sample_rate * duracao))

        for nota in notas:
            freq = NOTAS.get(nota.upper(), 0)
            if freq > 0:
                t = np.linspace(0, duracao, int(self.sample_rate * duracao), False)
                onda = np.sin(2 * np.pi * freq * t) * volume / len(notas)
                audio_total += onda

        # Normaliza
        audio_total = audio_total / np.max(np.abs(audio_total)) * 0.9

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, prefix="acorde_")
        arquivo = tmp.name
        tmp.close()

        sf.write(arquivo, audio_total, self.sample_rate, subtype='PCM_16')
        return arquivo

    def gerar_ruido(self, duracao: float = 1.0, tipo: str = "branco") -> Optional[str]:
        """Gera ruído (branco, rosa, marrom)."""
        if not _numpy_ok or not _soundfile_ok:
            return None

        samples = int(self.sample_rate * duracao)

        if tipo == "branco":
            audio = np.random.randn(samples) * 0.3
        elif tipo == "rosa":
            # Aproximação de ruído rosa
            audio = np.random.randn(samples) * 0.3
            # Filtro simples
            for i in range(1, len(audio)):
                audio[i] = audio[i-1] * 0.99 + audio[i] * 0.01
        elif tipo == "marrom":
            audio = np.random.randn(samples) * 0.3
            for i in range(1, len(audio)):
                audio[i] = audio[i-1] * 0.95 + audio[i] * 0.05
        else:
            audio = np.random.randn(samples) * 0.3

        # Normaliza
        audio = audio / np.max(np.abs(audio)) * 0.5

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False, prefix="ruido_")
        arquivo = tmp.name
        tmp.close()

        sf.write(arquivo, audio, self.sample_rate, subtype='PCM_16')
        return arquivo

    def analisar_audio(self, arquivo: str) -> Optional[Dict]:
        """Analisa propriedades do áudio."""
        if not _soundfile_ok or not _numpy_ok:
            return None

        try:
            audio, sr = sf.read(arquivo)
            duracao = len(audio) / sr

            # RMS (energia)
            rms = np.sqrt(np.mean(audio**2))

            # Pico
            pico = np.max(np.abs(audio))

            # Frequência dominante (FFT simples)
            if len(audio) > 1024:
                fft = np.fft.rfft(audio[:8192])
                freqs = np.fft.rfftfreq(len(audio[:8192]), 1/sr)
                magnitudes = np.abs(fft)
                idx_freq_max = np.argmax(magnitudes[1:]) + 1
                freq_dominante = freqs[idx_freq_max]
            else:
                freq_dominante = 0

            return {
                "duracao_seg": round(duracao, 2),
                "sample_rate": sr,
                "canais": 1 if len(audio.shape) == 1 else audio.shape[1],
                "rms": round(float(rms), 4),
                "pico": round(float(pico), 4),
                "freq_dominante_hz": round(float(freq_dominante), 2),
                "silencioso": rms < 0.01
            }
        except Exception as e:
            print(f"[MUSIC] Erro analisando: {e}")
            return None

    def converter_frequencia(self, nota: str) -> Optional[float]:
        """Converte nome da nota para frequência."""
        return NOTAS.get(nota.upper())

    def nota_para_frequencia(self, nota: str, oitava: int = 4) -> float:
        """Calcula frequência usando fórmula musical."""
        notas_semitom = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5,
                         "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0,
                         "A#": 1, "B": 2}

        nota_base = nota.rstrip("#b")
        if nota_base not in notas_semitom:
            return 0

        semitom = notas_semitom[nota_base]
        # A4 = 440Hz
        freq = 440 * (2 ** ((semitom + (oitava - 4) * 12) / 12))
        return freq

    def escalar_musical(self, tonica: str, escala: str = "maior") -> List[str]:
        """Gera escala musical."""
        intervalos = {
            "maior": [0, 2, 4, 5, 7, 9, 11],
            "menor": [0, 2, 3, 5, 7, 8, 10],
            "pentatonica": [0, 2, 4, 7, 9],
            "blues": [0, 3, 5, 6, 7, 10],
            "dorica": [0, 2, 3, 5, 7, 9, 10],
            "frigia": [0, 1, 3, 5, 7, 8, 10],
            "lidia": [0, 2, 4, 6, 7, 9, 11],
            "mixolidia": [0, 2, 4, 5, 7, 9, 10],
            "locria": [0, 1, 3, 5, 6, 8, 10],
        }

        notas = list(NOTAS.keys())
        if tonica not in notas:
            return []

        idx_tonica = notas.index(tonica)
        intervalos_escala = intervalos.get(escala, intervalos["maior"])

        escala_resultado = []
        for intervalo in intervalos_escala:
            idx = (idx_tonica + intervalo) % len(notas)
            escala_resultado.append(notas[idx])

        return escala_resultado

    def tocar_audio(self, arquivo: str):
        """Toca arquivo de áudio."""
        if not _pygame_ok:
            print("[MUSIC] Pygame necessário para reproduzir")
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            pygame.mixer.music.load(arquivo)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                import time
                time.sleep(0.1)
        except Exception as e:
            print(f"[MUSIC] Erro reproduzindo: {e}")

    def status(self) -> Dict:
        """Retorna status do gerador."""
        return {
            "numpy": _numpy_ok,
            "soundfile": _soundfile_ok,
            "pygame": _pygame_ok,
            "sample_rate": self.sample_rate,
            "notas_disponiveis": list(NOTAS.keys())
        }


# ═══ INSTANCIA GLOBAL ═══
_music_instance = None


def get_music_generator() -> MusicGenerator:
    """Retorna instância do Music Generator."""
    global _music_instance
    if _music_instance is None:
        _music_instance = MusicGenerator()
    return _music_instance
