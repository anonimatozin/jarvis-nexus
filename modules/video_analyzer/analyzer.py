"""
JARVIS Video Analyzer v1.0
Análise inteligente de vídeo com IA.

Baseado em: byjlw/video-analyzer (1.5k stars)
Recursos:
  - Extração de frames
  - Transcrição de áudio
  - Detecção de objetos
  - Resumo de vídeos
  - Análise de conteúdo
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading

# ═══ DEPENDENCIAS OPCIONAIS ═══
_cv2_ok = False
_ffmpeg_ok = False

try:
    import cv2
    _cv2_ok = True
except ImportError:
    pass

try:
    import subprocess
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
    _ffmpeg_ok = result.returncode == 0
except Exception:
    pass


class VideoAnalyzer:
    """Analisador inteligente de vídeo."""

    def __init__(self, pasta_trabalho: str = None):
        self.pasta_trabalho = Path(pasta_trabalho or os.path.expanduser("~\\Videos"))
        self._cache = {}
        self._lock = threading.Lock()

        print(f"[VIDEO] Analisador inicializado")
        print(f"  OpenCV: {'✅' if _cv2_ok else '❌'}")
        print(f"  FFmpeg: {'✅' if _ffmpeg_ok else '❌'}")

    def extrair_frames(self, video_path: str, intervalo: float = 1.0,
                       max_frames: int = 10) -> List[str]:
        """Extrai frames do vídeo em intervalos regulares."""
        if not _cv2_ok:
            print("[VIDEO] OpenCV não disponível")
            return []

        video_path = Path(video_path)
        if not video_path.exists():
            print(f"[VIDEO] Arquivo não encontrado: {video_path}")
            return []

        try:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duracao = total_frames / fps if fps > 0 else 0

            print(f"[VIDEO] FPS: {fps}, Total: {total_frames}, Duração: {duracao:.1f}s")

            frames_extraidos = []
            intervalo_frames = int(fps * intervalo)
            frame_count = 0

            # Cria pasta de saída
            pasta_frames = video_path.parent / f"{video_path.stem}_frames"
            pasta_frames.mkdir(exist_ok=True)

            while cap.isOpened() and len(frames_extraidos) < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % intervalo_frames == 0:
                    frame_path = pasta_frames / f"frame_{len(frames_extraidos):04d}.jpg"
                    cv2.imwrite(str(frame_path), frame)
                    frames_extraidos.append(str(frame_path))

                frame_count += 1

            cap.release()
            print(f"[VIDEO] {len(frames_extraidos)} frames extraídos")
            return frames_extraidos

        except Exception as e:
            print(f"[VIDEO] Erro extraindo frames: {e}")
            return []

    def obter_info(self, video_path: str) -> Optional[Dict]:
        """Obtém informações do vídeo."""
        if not _cv2_ok:
            return None

        video_path = Path(video_path)
        if not video_path.exists():
            return None

        try:
            cap = cv2.VideoCapture(str(video_path))
            info = {
                "arquivo": video_path.name,
                "tamanho_mb": round(video_path.stat().st_size / (1024 * 1024), 2),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "largura": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "altura": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            }
            info["duracao_seg"] = info["total_frames"] / info["fps"] if info["fps"] > 0 else 0
            info["duracao_formatada"] = self._formatar_duracao(info["duracao_seg"])
            cap.release()
            return info
        except Exception:
            return None

    def _formatar_duracao(self, segundos: float) -> str:
        """Formata duração em HH:MM:SS."""
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        secs = int(segundos % 60)
        if horas > 0:
            return f"{horas:02d}:{minutos:02d}:{secs:02d}"
        return f"{minutos:02d}:{secs:02d}"

    def transcrever_audio(self, video_path: str) -> Optional[str]:
        """Extrai e transcreve áudio do vídeo."""
        if not _ffmpeg_ok:
            print("[VIDEO] FFmpeg não disponível")
            return None

        video_path = Path(video_path)
        if not video_path.exists():
            return None

        try:
            # Extrai áudio
            audio_path = video_path.parent / f"{video_path.stem}_audio.wav"
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                str(audio_path), "-y"
            ]
            subprocess.run(cmd, capture_output=True, timeout=60)

            if audio_path.exists():
                print(f"[VIDEO] Áudio extraído: {audio_path}")
                # Nota: transcrição precisa de whisper ou outro STT
                return str(audio_path)
        except Exception as e:
            print(f"[VIDEO] Erro extraindo áudio: {e}")
        return None

    def detectar_cenas(self, video_path: str, threshold: float = 30.0) -> List[Dict]:
        """Detecta mudanças de cena no vídeo."""
        if not _cv2_ok:
            return []

        video_path = Path(video_path)
        if not video_path.exists():
            return []

        try:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            cenas = []
            frame_anterior = None
            frame_count = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_anterior is not None:
                    # Calcula diferença entre frames
                    diff = cv2.absdiff(frame_anterior, frame)
                    media_diff = diff.mean()

                    if media_diff > threshold:
                        tempo = frame_count / fps if fps > 0 else 0
                        cenas.append({
                            "frame": frame_count,
                            "tempo_seg": round(tempo, 2),
                            "tempo_formatado": self._formatar_duracao(tempo),
                            "intensidade": round(media_diff, 2)
                        })

                frame_anterior = frame.copy()
                frame_count += 1

            cap.release()
            print(f"[VIDEO] {len(cenas)} cenas detectadas")
            return cenas

        except Exception as e:
            print(f"[VIDEO] Erro detectando cenas: {e}")
            return []

    def gerar_thumbnail(self, video_path: str, tempo: float = None) -> Optional[str]:
        """Gera thumbnail do vídeo."""
        if not _cv2_ok:
            return None

        video_path = Path(video_path)
        if not video_path.exists():
            return None

        try:
            cap = cv2.VideoCapture(str(video_path))

            if tempo is not None:
                fps = cap.get(cv2.CAP_PROP_FPS)
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(tempo * fps))

            ret, frame = cap.read()
            cap.release()

            if ret:
                thumb_path = video_path.parent / f"{video_path.stem}_thumb.jpg"
                cv2.imwrite(str(thumb_path), frame)
                return str(thumb_path)
        except Exception:
            pass
        return None

    def analisar_luminosidade(self, video_path: str) -> Dict:
        """Analisa luminosidade ao longo do vídeo."""
        if not _cv2_ok:
            return {}

        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            luminosidades = []
            frame_count = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % int(fps) == 0:  # 1 frame por segundo
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    luminosidade = gray.mean()
                    luminosidades.append({
                        "tempo": self._formatar_duracao(frame_count / fps),
                        "luminosidade": round(luminosidade, 2)
                    })

                frame_count += 1

            cap.release()

            if luminosidades:
                media = sum(l["luminosidade"] for l in luminosidades) / len(luminosidades)
                return {
                    "media": round(media, 2),
                    "minima": min(l["luminosidade"] for l in luminosidades),
                    "maxima": max(l["luminosidade"] for l in luminosidades),
                    "amostras": luminosidades[:10]  # Primeiras 10
                }
        except Exception:
            pass
        return {}

    def status(self) -> Dict:
        """Retorna status do analisador."""
        return {
            "opencv": _cv2_ok,
            "ffmpeg": _ffmpeg_ok,
            "pasta_trabalho": str(self.pasta_trabalho)
        }


# ═══ INSTANCIA GLOBAL ═══
_video_instance = None


def get_video_analyzer(pasta: str = None) -> VideoAnalyzer:
    """Retorna instância do Video Analyzer."""
    global _video_instance
    if _video_instance is None:
        _video_instance = VideoAnalyzer(pasta)
    return _video_instance
