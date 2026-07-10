"""ConfigPanel v4 - com botao X interno e suporte ESC."""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget,
    QStackedWidget, QListWidgetItem, QScrollArea, QPushButton
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal

from .. import config as cfg

from .tabs.tab_geral import TabGeral
from .tabs.tab_voz import TabVoz
from .tabs.tab_mic import TabMic
from .tabs.tab_audio import TabAudio
from .tabs.tab_ia import TabIA
from .tabs.tab_memoria import TabMemoria
from .tabs.tab_sobre import TabSobre


class ConfigPanel(QWidget):
    sig_closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("configPanel")
        self.setFixedWidth(cfg.CONFIG_PANEL_WIDTH)
        self._is_open = False
        self._animating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header com titulo + botao X
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        title = QLabel("CONFIGURACOES")
        title.setObjectName("configTitle")
        header_layout.addWidget(title, 1)

        self.btn_close = QPushButton("X")
        self.btn_close.setObjectName("panelCloseBtn")
        self.btn_close.setFixedSize(40, 40)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setToolTip("Fechar (ESC)")
        self.btn_close.clicked.connect(self.hide_panel)
        header_layout.addWidget(self.btn_close)

        layout.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.tab_list = QListWidget()
        self.tab_list.setObjectName("tabList")
        self.tab_list.setFixedWidth(130)
        items = ["Geral", "Voz", "Microfone", "Audio", "IA", "Memoria", "Sobre"]
        for i in items:
            QListWidgetItem(i, self.tab_list)
        body.addWidget(self.tab_list)

        self.stack = QStackedWidget()
        self.stack.setObjectName("tabContent")

        def wrap(widget):
            scroll = QScrollArea()
            scroll.setWidget(widget)
            scroll.setWidgetResizable(True)
            return scroll

        self.stack.addWidget(wrap(TabGeral()))
        self.stack.addWidget(wrap(TabVoz()))
        self.stack.addWidget(wrap(TabMic()))
        self.stack.addWidget(wrap(TabAudio()))
        self.stack.addWidget(wrap(TabIA()))
        self.stack.addWidget(wrap(TabMemoria()))
        self.stack.addWidget(wrap(TabSobre()))

        body.addWidget(self.stack, 1)
        layout.addLayout(body)

        self.tab_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.tab_list.setCurrentRow(0)

        self._anim = None
        self.hide()

    def keyPressEvent(self, event):
        """ESC fecha."""
        if event.key() == Qt.Key_Escape:
            self.hide_panel()
        else:
            super().keyPressEvent(event)

    def toggle(self):
        if self._animating:
            return
        if self._is_open:
            self.hide_panel()
        else:
            self.show_panel()

    def show_panel(self):
        if self._animating or self._is_open:
            return
        parent = self.parent()
        if not parent:
            self.show()
            return

        self._animating = True
        self.show()
        self.raise_()
        self.setFocus()

        end_x = parent.width() - self.width()
        start_x = parent.width()

        self.setGeometry(start_x, 0, self.width(), parent.height())

        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(220)
        self._anim.setStartValue(QRect(start_x, 0, self.width(), parent.height()))
        self._anim.setEndValue(QRect(end_x, 0, self.width(), parent.height()))
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.finished.connect(self._on_show_done)
        self._anim.start()

    def _on_show_done(self):
        self._animating = False
        self._is_open = True

    def hide_panel(self):
        if self._animating or not self._is_open:
            return
        parent = self.parent()
        if not parent:
            self.hide()
            self._is_open = False
            return

        self._animating = True
        end_x = parent.width()
        start_x = self.x() if 0 <= self.x() < parent.width() else parent.width() - self.width()

        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(180)
        self._anim.setStartValue(QRect(start_x, 0, self.width(), parent.height()))
        self._anim.setEndValue(QRect(end_x, 0, self.width(), parent.height()))
        self._anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim.finished.connect(self._on_hide_done)
        self._anim.start()

    def _on_hide_done(self):
        self.hide()
        self._is_open = False
        self._animating = False
        self.sig_closed.emit()

    def reposition(self):
        parent = self.parent()
        if parent and self._is_open and not self._animating:
            end_x = parent.width() - self.width()
            self.setGeometry(end_x, 0, self.width(), parent.height())

    def is_open(self):
        return self._is_open

    def contains_point(self, global_point):
        """Verifica se ponto global esta dentro do painel."""
        if not self._is_open:
            return False
        local = self.mapFromGlobal(global_point)
        return self.rect().contains(local)
