"""
MiniOrb - janela 150x150 always-on-top.
Aparece quando o HUD principal minimiza.
Clica nele -> abre HUD fullscreen.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, Signal, QPoint

from .orb import Orb
from .. import config as cfg


class MiniOrb(QWidget):
    sig_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Frameless + sempre no topo + sem barra
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool  # nao aparece na taskbar
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(cfg.MINI_ORB_SIZE, cfg.MINI_ORB_SIZE)

        # Container com fundo arredondado
        self.bg = QWidget(self)
        self.bg.setObjectName("miniOrbBg")
        self.bg.setGeometry(0, 0, cfg.MINI_ORB_SIZE, cfg.MINI_ORB_SIZE)

        layout = QVBoxLayout(self.bg)
        layout.setContentsMargins(8, 8, 8, 8)

        self.orb = Orb()
        self.orb.setMinimumSize(cfg.MINI_ORB_SIZE - 30, cfg.MINI_ORB_SIZE - 30)
        self.orb.setMaximumSize(cfg.MINI_ORB_SIZE - 30, cfg.MINI_ORB_SIZE - 30)
        layout.addWidget(self.orb)

        self._drag_pos = None
        self._drag_started = False
        self._restore_to_canto()

    def _restore_to_canto(self):
        """Posiciona no canto inferior direito (ou ultima posicao salva)."""
        saved = cfg.get("mini_orb_position", [None, None])
        if saved and saved[0] is not None:
            self.move(saved[0], saved[1])
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            x = screen.width() - cfg.MINI_ORB_SIZE - 20
            y = screen.height() - cfg.MINI_ORB_SIZE - 20
            self.move(x, y)

    def set_state(self, state):
        self.orb.set_state(state)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._drag_started = False
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._drag_pos:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            old_pos = self.pos()
            # Se moveu mais que 5px, eh drag
            if (abs(new_pos.x() - old_pos.x()) + abs(new_pos.y() - old_pos.y())) > 5:
                self._drag_started = True
                self.move(new_pos)
                event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self._drag_started:
                # Foi clique simples -> emite sinal
                self.sig_clicked.emit()
            else:
                # Salva nova posicao
                cfg.set_value("mini_orb_position", [self.x(), self.y()])
            self._drag_pos = None
            self._drag_started = False
            event.accept()
