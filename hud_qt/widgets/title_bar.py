"""TitleBar v3.0 - Stark Reactor Pro"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt

from .. import config as cfg


class TitleBar(QWidget):
    sig_config = Signal()
    sig_minimize = Signal()
    sig_maximize = Signal()
    sig_close = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(cfg.TITLE_BAR_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.brand = QLabel("J.A.R.V.I.S.")
        self.brand.setObjectName("brandLabel")
        layout.addWidget(self.brand)

        layout.addStretch()

        self.btn_config = QPushButton("\u22EE")
        self.btn_config.setObjectName("titleBtn")
        self.btn_config.setToolTip("Configuracoes")
        self.btn_config.clicked.connect(self.sig_config.emit)
        layout.addWidget(self.btn_config)

        self.btn_min = QPushButton("\u2014")
        self.btn_min.setObjectName("titleBtn")
        self.btn_min.setToolTip("Minimizar (Win+J)")
        self.btn_min.clicked.connect(self.sig_minimize.emit)
        layout.addWidget(self.btn_min)

        self.btn_max = QPushButton("\u25A1")
        self.btn_max.setObjectName("titleBtn")
        self.btn_max.setToolTip("Maximizar / Restaurar")
        self.btn_max.clicked.connect(self.sig_maximize.emit)
        layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("\u2715")
        self.btn_close.setObjectName("titleBtnClose")
        self.btn_close.setToolTip("Encerrar Jarvis")
        self.btn_close.clicked.connect(self.sig_close.emit)
        layout.addWidget(self.btn_close)
