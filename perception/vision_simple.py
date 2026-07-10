# perception/vision_simple.py
import cv2
import time
import threading
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logger import print_success, print_system, print_error

class JarvisVisionSimple:
    def __init__(self):
        self.camera = None
        self.is_running = False
        self.callback = None
        self.face_cascade = None
        
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            print_error("Classificador facial não carregado")
        else:
            print_success("Detector facial OpenCV carregado.")
            
        self._init_camera()
        
    def _init_camera(self):
        try:
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.camera.isOpened():
                print_error("Câmera não encontrada")
                self.camera = None
            else:
                print_success("Câmera inicializada.")
        except Exception as e:
            print_error(f"Erro ao abrir câmera: {e}")
            self.camera = None
            
    def capture_frame(self):
        if self.camera is None or not self.camera.isOpened():
            return None
        ret, frame = self.camera.read()
        return frame if ret else None
        
    def count_faces(self):
        frame = self.capture_frame()
        if frame is None:
            return 0
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
        return len(faces)
        
    def start_monitoring(self, callback=None, interval=2):
        self.is_running = True
        self.callback = callback
        
        def monitor():
            last_count = 0
            while self.is_running:
                count = self.count_faces()
                if count != last_count and self.callback:
                    self.callback({"type": "face_change", "count": count, "has_face": count > 0})
                last_count = count
                time.sleep(interval)
                
        threading.Thread(target=monitor, daemon=True).start()
        print_success(f"Monitoramento facial ativo")
        
    def stop_monitoring(self):
        self.is_running = False
        if self.camera:
            self.camera.release()
        print_system("Monitoramento facial desativado.")