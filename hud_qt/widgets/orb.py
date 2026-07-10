"""
ORB v4.0 - Stark Reactor Pro
Coracao visual do Jarvis com animacoes profissionais.
"""
import math
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient

from .. import config as cfg


class Orb(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(cfg.ORB_MIN_SIZE, cfg.ORB_MIN_SIZE)
        self.state = "idle"

        self.t = 0.0
        self.pulse = 0.0
        self.pulse_dir = 1
        self.rotation = 0.0
        self.wave_phase = 0.0
        self.particles = []
        self._init_particles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16)

        self.setAttribute(Qt.WA_TranslucentBackground)

    def _init_particles(self):
        self.particles = []
        for i in range(14):
            self.particles.append({
                "angle": random.uniform(0, 360),
                "radius_ratio": random.uniform(0.5, 0.92),
                "speed": random.uniform(0.6, 2.8),
                "size": random.uniform(1.5, 3.5),
                "alpha": random.randint(80, 220),
                "phase": random.uniform(0, 360),
            })

    def set_state(self, state):
        if state not in ("idle", "listening", "thinking", "speaking"):
            return
        old = self.state
        self.state = state
        if state == "thinking" and old != "thinking":
            self.rotation = 0.0

    def _animate(self):
        self.t += 0.016

        self.pulse += 0.012 * self.pulse_dir
        if self.pulse > 1.0:
            self.pulse_dir = -1
        elif self.pulse < 0.0:
            self.pulse_dir = 1

        if self.state == "thinking":
            self.rotation = (self.rotation + 1.8) % 360
            for p in self.particles:
                p["angle"] = (p["angle"] + p["speed"]) % 360
        elif self.state == "listening":
            self.wave_phase = (self.wave_phase + 0.03) % 1.0
        elif self.state == "speaking":
            self.pulse += 0.025 * self.pulse_dir
            self.rotation = (self.rotation + 0.8) % 360

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        size = min(w, h)
        p = cfg.PALETA

        cor_map = {
            "idle": p["orb_idle"],
            "listening": p["orb_listen"],
            "thinking": p["orb_think"],
            "speaking": p["orb_speak"],
        }
        cor = QColor(cor_map.get(self.state, p["orb_idle"]))

        if self.state == "idle":
            breath = math.sin(self.t * 0.7) * 0.03 + 0.5
        elif self.state == "speaking":
            breath = math.sin(self.t * 5) * 0.1 + 0.55
        elif self.state == "listening":
            breath = 0.5 + math.sin(self.t * 1.5) * 0.02
        else:
            breath = 0.5 + self.pulse * 0.06

        nucleo_size = size * 0.2 * (1 + breath * 0.2)

        # Halo externo
        halo_size = size * 0.9
        halo_grad = QRadialGradient(cx, cy, halo_size / 2)
        halo_c = QColor(cor)
        halo_c.setAlpha(int(20 + self.pulse * 20))
        halo_grad.setColorAt(0, halo_c)
        halo_grad.setColorAt(0.6, QColor(cor.red(), cor.green(), cor.blue(), 5))
        transparent = QColor(cor)
        transparent.setAlpha(0)
        halo_grad.setColorAt(1, transparent)
        painter.setBrush(QBrush(halo_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - halo_size/2, cy - halo_size/2, halo_size, halo_size))

        # Listening - ondas
        if self.state == "listening":
            for i in range(3):
                phase = (self.wave_phase + i * 0.33) % 1.0
                ws = size * (0.25 + phase * 0.5)
                wa = int(90 * (1 - phase))
                wc = QColor(cor)
                wc.setAlpha(wa)
                pen = QPen(wc, 1.2 + (1 - phase))
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QRectF(cx - ws/2, cy - ws/2, ws, ws))

        # Thinking - particulas + anel
        if self.state == "thinking":
            for part in self.particles:
                ar = math.radians(part["angle"])
                radius = (size * 0.36) * part["radius_ratio"]
                px = cx + math.cos(ar) * radius
                py = cy + math.sin(ar) * radius
                pc = QColor(cor)
                pc.setAlpha(part["alpha"])
                painter.setBrush(QBrush(pc))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QRectF(px - part["size"]/2, py - part["size"]/2,
                                           part["size"], part["size"]))
            rs = size * 0.65
            rc = QColor(cor)
            rc.setAlpha(50)
            pen = QPen(rc, 0.8, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(self.rotation)
            painter.drawEllipse(QRectF(-rs/2, -rs/2, rs, rs))
            painter.restore()

        # Speaking - ondas internas
        if self.state == "speaking":
            for i in range(2):
                phase = (self.t * 1.2 + i * 0.5) % 1.0
                ws2 = size * (0.28 + phase * 0.4)
                wa2 = int(60 * (1 - phase))
                wc2 = QColor(cor)
                wc2.setAlpha(wa2)
                pen2 = QPen(wc2, 1)
                painter.setPen(pen2)
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QRectF(cx - ws2/2, cy - ws2/2, ws2, ws2))

        # Anel estatico
        anel_s = size * 0.48
        anel_c = QColor(cor)
        anel_c.setAlpha(30)
        painter.setPen(QPen(anel_c, 0.6))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - anel_s/2, cy - anel_s/2, anel_s, anel_s))

        # Nucleo
        nuc_grad = QRadialGradient(cx, cy, nucleo_size / 2)
        nuc_grad.setColorAt(0, QColor(255, 255, 255, 230))
        bright = QColor(min(255, cor.red() + 70),
                        min(255, cor.green() + 70),
                        min(255, cor.blue() + 70))
        nuc_grad.setColorAt(0.3, bright)
        nuc_grad.setColorAt(0.65, cor)
        nuc_grad.setColorAt(1, QColor(cor.red(), cor.green(), cor.blue(), 0))
        painter.setBrush(QBrush(nuc_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - nucleo_size/2, cy - nucleo_size/2,
                                    nucleo_size, nucleo_size))

        # Brilho central
        b_size = nucleo_size * 0.28
        b_grad = QRadialGradient(cx - nucleo_size*0.06, cy - nucleo_size*0.06, b_size/2)
        b_grad.setColorAt(0, QColor(255, 255, 255, 200))
        b_grad.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(b_grad))
        painter.drawEllipse(QRectF(cx - b_size/2, cy - b_size/2, b_size, b_size))
