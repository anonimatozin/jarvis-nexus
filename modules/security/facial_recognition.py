# modules/security/facial_recognition.py
"""
J.A.R.V.I.S. - Facial Recognition Module
Autenticacao por reconhecimento facial usando OpenCV LBPH.
Inspirado no vannu07/jarvis.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime

class FacialRecognition:
    """Sistema de autenticacao por reconhecimento facial."""
    
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.faces_dir = self.data_dir / "faces"
        self.faces_dir.mkdir(exist_ok=True)
        
        self.model_path = self.data_dir / "face_model.yml"
        self.labels_file = self.data_dir / "face_labels.json"
        
        self.labels = self._load_labels()
        self.recognizer = None
        self.face_cascade = None
        self.initialized = False
        
        self._init_opencv()
    
    def _load_labels(self):
        """Carrega labels dos rostos cadastrados."""
        try:
            if self.labels_file.exists():
                with open(self.labels_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_labels(self):
        """Salva labels dos rostos."""
        with open(self.labels_file, 'w') as f:
            json.dump(self.labels, f, indent=2)
    
    def _init_opencv(self):
        """Inicializa componentes do OpenCV."""
        try:
            import cv2
            
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            
            # Tenta carregar modelo existente
            if self.model_path.exists():
                self.recognizer.read(str(self.model_path))
                self.initialized = True
            
        except ImportError:
            print("[FACIAL] OpenCV nao instalado. pip install opencv-python")
        except Exception as e:
            print(f"[FACIAL] Erro ao inicializar: {e}")
    
    def register_face(self, name, num_samples=20):
        """Cadastra um novo rosto."""
        if not self.initialized:
            return "OpenCV nao inicializado."
        
        try:
            import cv2
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return "Camera nao encontrada."
            
            faces = []
            labels = []
            label_id = len(self.labels)
            
            print(f"[FACIAL] Cadastrando {name}. Olhe para a camera...")
            print(f"[FACIAL] Coletando {num_samples} amostras...")
            
            count = 0
            while count < num_samples:
                ret, frame = cap.read()
                if not ret:
                    continue
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces_detected = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in faces_detected:
                    face_img = gray[y:y+h, x:x+w]
                    face_resized = cv2.resize(face_img, (200, 200))
                    
                    faces.append(face_resized)
                    labels.append(label_id)
                    count += 1
                    
                    # Mostra progresso
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"Amostra {count}/{num_samples}", 
                               (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow('Cadastro de Rosto - ESC para cancelar', frame)
                
                if cv2.waitKey(1) == 27:  # ESC
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            if count < 5:
                return "Amostras insuficientes. Tente novamente."
            
            # Treina o reconhecedor
            self.recognizer.train(faces, [label_id] * len(faces))
            
            # Salva modelo e label
            self.labels[str(label_id)] = name
            self._save_labels()
            
            # Salva modelo
            import cv2
            recognizer_new = cv2.face.LBPHFaceRecognizer_create()
            recognizer_new.train(faces, [label_id] * len(faces))
            
            # Se ja existe modelo, treina com todos
            if self.model_path.exists():
                # Por simplicidade, salva apenas o novo
                recognizer_new.write(str(self.model_path))
            else:
                recognizer_new.write(str(self.model_path))
            
            self.initialized = True
            return f"Rosto de '{name}' cadastrado com {count} amostras."
            
        except Exception as e:
            return f"Erro no cadastro: {e}"
    
    def recognize_face(self):
        """Reconhece um rosto na camera."""
        if not self.initialized:
            return None, "Modelo nao treinado. Cadastre um rosto primeiro."
        
        try:
            import cv2
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return None, "Camera nao encontrada."
            
            result = None
            start_time = time.time()
            
            while time.time() - start_time < 5:  # Tenta por 5 segundos
                ret, frame = cap.read()
                if not ret:
                    continue
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in faces:
                    face_img = gray[y:y+h, x:x+w]
                    face_resized = cv2.resize(face_img, (200, 200))
                    
                    label_id, confidence = self.recognizer.predict(face_resized)
                    
                    if confidence < 70:  # Boa confianca
                        name = self.labels.get(str(label_id), "Desconhecido")
                        result = {
                            'name': name,
                            'confidence': round(100 - confidence, 1),
                            'authorized': confidence < 50
                        }
                        break
                
                if result:
                    break
                
                cv2.imshow('Reconhecimento Facial - ESC para cancelar', frame)
                if cv2.waitKey(1) == 27:
                    break
            
            cap.release()
            cv2.destroyAllWindows()
            
            if result:
                return result, None
            return None, "Rosto nao reconhecido."
            
        except Exception as e:
            return None, f"Erro no reconhecimento: {e}"
    
    def list_registered_faces(self):
        """Lista rostos cadastrados."""
        if not self.labels:
            return "Nenhum rosto cadastrado."
        
        faces = []
        for label_id, name in self.labels.items():
            faces.append(f"ID {label_id}: {name}")
        
        return "\n".join(faces)
    
    def delete_face(self, name):
        """Remove um rosto cadastrado."""
        for label_id, label_name in self.labels.items():
            if label_name.lower() == name.lower():
                del self.labels[label_id]
                self._save_labels()
                return f"Rosto '{name}' removido."
        return f"Rosto '{name}' nao encontrado."
    
    def authenticate(self, required_name=None):
        """Autentica usuario por rosto."""
        result, error = self.recognize_face()
        
        if error:
            return False, error
        
        if required_name and result['name'].lower() != required_name.lower():
            return False, f"Rosto nao corresponde a '{required_name}'."
        
        if result['authorized']:
            return True, f"Bem-vindo, {result['name']}! (Confianca: {result['confidence']}%)"
        else:
            return False, f"Confianca insuficiente: {result['confidence']}%"


def criar_modulo_facial():
    """Retorna instancia do modulo facial."""
    return FacialRecognition()
