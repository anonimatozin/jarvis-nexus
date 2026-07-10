"""
PopupCamera - Janela flutuante mostrando stream RTSP ao vivo.
"""
import os
# CRITICO: TCP + timeout 10s pra cameras Yoosee/ONVIF
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;10000000"
import cv2
import threading
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QApplication
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QThread, QSize
)
from PySide6.QtGui import (
    QPixmap, QImage, QColor, QPainter, QPainterPath, QPen
)


class StreamThread(QThread):
    """Thread que le frames da camera RTSP."""
    frame_pronto = Signal(QImage)

    def __init__(self, rtsp_url):
        super().__init__()
        self.url = rtsp_url
        self.rodando = True

    def run(self):
        cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            print(f"[STREAM] erro abrir {self.url}")
            return

        while self.rodando:
            ret, frame = cap.read()
            if not ret:
                self.msleep(100)
                continue

            # Converte BGR -> RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            # Importante: copia pra evitar reference do buffer
            self.frame_pronto.emit(qimg.copy())
            self.msleep(33)  # ~30 fps

        cap.release()

    def parar(self):
        self.rodando = False
        self.wait(2000)


class PopupCamera(QWidget):
    """Janela flutuante com stream ao vivo de camera."""

    sig_fechado = Signal()

    def __init__(self, nome, rtsp_url, fullscreen=False):
        super().__init__(None)
        self.nome = nome
        self.url = rtsp_url
        self.fullscreen = fullscreen

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        if fullscreen:
            self.setFixedSize(1280, 720)
        else:
            self.setFixedSize(560, 380)

        self._setup_ui()
        self._iniciar_stream()
        self._posicionar()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(12, 6, 12, 6)

        self.lbl_titulo = QLabel(f"📹 CAMERA · {self.nome.upper()}")
        self.lbl_titulo.setStyleSheet("""
            color: #ffffff;
            font-family: 'Segoe UI';
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 2px;
            background: rgba(0,0,0,200);
            padding: 4px 12px;
            border-radius: 4px;
        """)
        header.addWidget(self.lbl_titulo)
        header.addStretch()

        # Botao fullscreen toggle
        self.btn_full = QPushButton("⛶")
        self.btn_full.setFixedSize(28, 28)
        self.btn_full.setCursor(Qt.PointingHandCursor)
        self.btn_full.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,180);
                color: #fff; border: 1px solid #4da6ff;
                border-radius: 14px; font-size: 14px;
            }
            QPushButton:hover { background: rgba(77,166,255,180); }
        """)
        self.btn_full.clicked.connect(self._toggle_full)
        header.addWidget(self.btn_full)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,180);
                color: #fff; border: 1px solid rgba(255,255,255,80);
                border-radius: 14px; font-size: 12px;
            }
            QPushButton:hover { background: rgba(220,60,60,200); }
        """)
        self.btn_close.clicked.connect(self.fechar)
        header.addWidget(self.btn_close)

        # Video display
        self.lbl_video = QLabel()
        self.lbl_video.setAlignment(Qt.AlignCenter)
        self.lbl_video.setStyleSheet("background: #000;")
        self.lbl_video.setText("Conectando...")
        self.lbl_video.setStyleSheet(
            "background: #000; color: #4da6ff; font-size: 14px;"
        )

        # Wrapper pro header ficar sobreposto ao video
        layout.addWidget(self.lbl_video, 1)

        # Header como overlay no topo
        self.header_widget = QWidget(self.lbl_video)
        self.header_widget.setLayout(header)
        self.header_widget.setGeometry(0, 0, self.width(), 40)
        self.header_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def _posicionar(self):
        screen = QApplication.primaryScreen().availableGeometry()
        if self.fullscreen:
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
        else:
            x = screen.right() - self.width() - 20
            y = screen.top() + 60
        self.move(x, y)

    def _iniciar_stream(self):
        self.thread = StreamThread(self.url)
        self.thread.frame_pronto.connect(self._on_frame)
        self.thread.start()

    def _on_frame(self, qimg):
        try:
            pix = QPixmap.fromImage(qimg)
            scaled = pix.scaled(
                self.lbl_video.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.lbl_video.setPixmap(scaled)
        except: pass

    def _toggle_full(self):
        if self.fullscreen:
            self.fullscreen = False
            self.setFixedSize(560, 380)
        else:
            self.fullscreen = True
            self.setFixedSize(1280, 720)
        self.header_widget.setGeometry(0, 0, self.width(), 40)
        self._posicionar()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 10, 10)
        painter.setClipPath(path)
        painter.fillRect(self.rect(), QColor(10, 10, 15))

        # Borda neon
        pen = QPen(QColor(77, 166, 255, 200), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 9, 9)

    def fechar(self):
        try:
            self.thread.parar()
        except: pass
        self.hide()
        self.sig_fechado.emit()
        self.deleteLater()
