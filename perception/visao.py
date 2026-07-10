"""
NEXUS - Visao Computacional v4.1
Camera + leitura tela + OCR + multiplas cameras (IRIUN).
"""

import os
import time
from pathlib import Path
from typing import Optional, List, Dict

try:
    import cv2
    OPENCV_OK = True
except ImportError:
    OPENCV_OK = False

try:
    import mss
    import numpy as np
    SCREEN_OK = True
except ImportError:
    SCREEN_OK = False

OCR_OK = False
try:
    import pytesseract
    TESSERACT_PATHS = [
        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
        os.path.expanduser(r"~\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe"),
    ]
    for path in TESSERACT_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            OCR_OK = True
            print(f"Tesseract OK: {path}")
            break
except ImportError:
    pass


class Visao:
    """Sistema de percepcao visual."""
    
    def __init__(self, camera_id=0):
        self.camera = None
        self.camera_id = camera_id
        self.camera_atual_nome = ""
        self.sct = None
        self.face_cascade = None
        self.cameras_disponiveis = []
        
        if OPENCV_OK:
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
            except Exception:
                pass
            self._listar_cameras()
            self._tentar_camera()
        
        if SCREEN_OK:
            self.sct = mss.mss()
    
    def _listar_cameras(self):
        """Lista cameras disponiveis."""
        self.cameras_disponiveis = []
        for i in range(5):
            try:
                cam = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cam.isOpened():
                    ret, _ = cam.read()
                    if ret:
                        w = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        self.cameras_disponiveis.append({
                            "index": i,
                            "resolution": f"{w}x{h}",
                        })
                    cam.release()
            except Exception:
                pass
        
        if self.cameras_disponiveis:
            print(f"Cameras detectadas: {len(self.cameras_disponiveis)}")
            for c in self.cameras_disponiveis:
                idx = c["index"]
                res = c["resolution"]
                marca = " <-- ATUAL" if idx == self.camera_id else ""
                print(f"  Camera {idx} - {res}{marca}")
    
    def _tentar_camera(self):
        """Abre a camera escolhida."""
        if not OPENCV_OK:
            return False
        
        backends = [
            (cv2.CAP_DSHOW, "DirectShow"),
            (cv2.CAP_MSMF, "Media Foundation"),
            (cv2.CAP_ANY, "Auto"),
        ]
        
        for backend, nome in backends:
            try:
                cam = cv2.VideoCapture(self.camera_id, backend)
                if cam.isOpened():
                    for _ in range(5):
                        ret, frame = cam.read()
                        if ret and frame is not None and frame.size > 0:
                            self.camera = cam
                            self.camera_atual_nome = f"Camera {self.camera_id} ({nome})"
                            print(f"Camera {self.camera_id} OK (backend: {nome})")
                            return True
                        time.sleep(0.1)
                    cam.release()
            except Exception:
                pass
        
        print(f"Camera {self.camera_id} indisponivel.")
        return False
    
    def trocar_camera(self, novo_id):
        """Troca para outra camera."""
        if self.camera:
            try:
                self.camera.release()
            except Exception:
                pass
            self.camera = None
        
        self.camera_id = novo_id
        if self._tentar_camera():
            return f"Camera alterada para a numero {novo_id}, Sir."
        return f"Nao consegui abrir a camera {novo_id}."
    
    def listar_cameras_disponiveis(self):
        """Retorna texto com lista de cameras."""
        self._listar_cameras()
        if not self.cameras_disponiveis:
            return "Nenhuma camera detectada."
        
        linhas = [f"Tenho {len(self.cameras_disponiveis)} cameras disponiveis:"]
        for c in self.cameras_disponiveis:
            idx = c["index"]
            res = c["resolution"]
            marca = " (atual)" if idx == self.camera_id else ""
            linhas.append(f"Camera {idx}: {res}{marca}")
        return " | ".join(linhas)
    
    def _garantir_camera(self):
        if self.camera is None or not self.camera.isOpened():
            return self._tentar_camera()
        return True
    
    # ===== CAMERA =====
    
    def tirar_foto(self, path="foto.jpg"):
        if not self._garantir_camera():
            return None
        try:
            for _ in range(3):
                self.camera.read()
            ret, frame = self.camera.read()
            if ret and frame is not None:
                cv2.imwrite(path, frame)
                return path
        except Exception as e:
            print(f"Erro foto: {e}")
        return None
    
    def contar_rostos(self):
        if not self._garantir_camera():
            return 0
        if self.face_cascade is None:
            return 0
        try:
            melhor = 0
            for _ in range(3):
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)
                faces = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40)
                )
                if len(faces) > melhor:
                    melhor = len(faces)
                time.sleep(0.1)
            return melhor
        except Exception as e:
            print(f"Erro contar_rostos: {e}")
            return 0
    
    def detectar_presenca(self, timeout=2.0):
        return self.contar_rostos() > 0
    
    def descrever_camera(self):
        if not self._garantir_camera():
            return "Camera nao esta disponivel."
        rostos = self.contar_rostos()
        if rostos == 0:
            try:
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    return "Camera conectada mas nao consigo capturar imagem."
                if frame.mean() < 10:
                    return "Imagem muito escura. Verifique iluminacao."
                return "Nao detectei rostos. Pode estar muito longe ou angulo ruim."
            except Exception:
                pass
            return "Nao vejo ninguem, Sir."
        if rostos == 1:
            return "Vejo uma pessoa na sua frente, Sir."
        return f"Vejo {rostos} pessoas, Sir."
    
    # ===== TELA =====
    
    def capturar_tela(self, path="tela.png"):
        if not SCREEN_OK:
            return None
        try:
            monitor = self.sct.monitors[1]
            img = self.sct.grab(monitor)
            mss.tools.to_png(img.rgb, img.size, output=path)
            return path
        except Exception as e:
            print(f"Erro screenshot: {e}")
            return None
    
    def ler_tela(self):
        if not OCR_OK or not SCREEN_OK:
            return ""
        try:
            monitor = self.sct.monitors[1]
            img = self.sct.grab(monitor)
            arr = np.array(img)
            arr_bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
            gray = cv2.cvtColor(arr_bgr, cv2.COLOR_BGR2GRAY)
            try:
                texto = pytesseract.image_to_string(gray, lang="por")
            except Exception:
                texto = pytesseract.image_to_string(gray, lang="eng")
            return texto.strip()
        except Exception as e:
            return f"Erro OCR: {e}"
    
    def analisar_tela_visual(self):
        """Analisa caracteristicas visuais da tela."""
        if not SCREEN_OK:
            return {}
        try:
            monitor = self.sct.monitors[1]
            img = self.sct.grab(monitor)
            arr = np.array(img)
            arr_bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
            altura, largura = arr_bgr.shape[:2]
            brilho = arr_bgr.mean()
            sat = cv2.cvtColor(arr_bgr, cv2.COLOR_BGR2HSV)[:,:,1].mean()
            gray = cv2.cvtColor(arr_bgr, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            num_edges = edges.sum() / 255
            
            return {
                "resolucao": f"{largura}x{altura}",
                "brilho": round(brilho, 1),
                "saturacao": round(sat, 1),
                "complexidade": int(num_edges),
                "tema": "escuro" if brilho < 80 else "claro" if brilho > 180 else "medio",
            }
        except Exception as e:
            print(f"Erro analise visual: {e}")
            return {}
    
    def descrever_tela(self, brain=None):
        """Le E analisa visualmente, depois resume com IA."""
        texto = self.ler_tela()
        analise = self.analisar_tela_visual()
        
        contexto = []
        if analise:
            contexto.append(f"Resolucao da tela: {analise.get('resolucao', '?')}")
            contexto.append(f"Tema visual: {analise.get('tema', '?')}")
            contexto.append(f"Brilho medio: {analise.get('brilho', 0)}/255")
            contexto.append(f"Complexidade visual: {analise.get('complexidade', 0)}")
        
        if texto and len(texto) > 10:
            contexto.append(f"Texto extraido por OCR:\n{texto[:1500]}")
        
        info = "\n".join(contexto)
        
        if not info:
            return "Nao consegui analisar a tela."
        
        if brain:
            try:
                prompt = (
                    "Voce e o Jarvis analisando a tela do PC. "
                    "Baseado nas informacoes abaixo, descreva em 2-3 frases CURTAS "
                    "e NATURAIS o que provavelmente esta acontecendo. "
                    "Considere: que aplicativo/site esta aberto, o que o usuario "
                    "parece estar fazendo, e algo notavel (video, codigo, navegador). "
                    "Responda como Jarvis: direto e util. NAO repita o texto OCR, "
                    "INTERPRETE-O.\n\n"
                    f"INFORMACOES:\n{info}\n\n"
                    "Sua descricao em portugues (2-3 frases):"
                )
                resposta = brain.think(prompt)
                if resposta and len(resposta) > 15:
                    return resposta
            except Exception as e:
                print(f"Erro analise IA: {e}")
        
        if texto:
            return f"Texto visivel: {texto[:200]}..."
        return "Tela detectada mas sem texto legivel."
    
    # ===== CLEANUP =====
    
    def fechar(self):
        if self.camera:
            try:
                self.camera.release()
            except Exception:
                pass
            self.camera = None
        if self.sct:
            try:
                self.sct.close()
            except Exception:
                pass
    
    def __del__(self):
        self.fechar()
