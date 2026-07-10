"""Aba MICROFONE."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QComboBox,
    QHBoxLayout, QPushButton, QSpinBox
)
from PySide6.QtCore import Qt

from ... import config as cfg


class TabMic(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(6)

        sec1 = QLabel("WAKE WORD")
        sec1.setObjectName("tabSection")
        layout.addWidget(sec1)

        ww_row = QHBoxLayout()
        ww_lbl = QLabel("Palavra de ativacao:")
        ww_lbl.setObjectName("fieldLabel")
        ww_row.addWidget(ww_lbl)
        ww_row.addStretch()
        self.cb_ww = QComboBox()
        self.cb_ww.addItems(["jarvis", "computador", "assistente"])
        atual = cfg.get("wake_word", "jarvis")
        idx = self.cb_ww.findText(atual)
        if idx >= 0: self.cb_ww.setCurrentIndex(idx)
        self.cb_ww.currentTextChanged.connect(
            lambda v: cfg.set_value("wake_word", v)
        )
        ww_row.addWidget(self.cb_ww)
        layout.addLayout(ww_row)

        hint = QLabel("Aplicado na proxima reinicializacao.")
        hint.setObjectName("fieldHint")
        layout.addWidget(hint)

        sec2 = QLabel("TIMEOUT DE COMANDO")
        sec2.setObjectName("tabSection")
        layout.addWidget(sec2)

        to_row = QHBoxLayout()
        to_lbl = QLabel("Apos wake word, ouvir por:")
        to_lbl.setObjectName("fieldLabel")
        to_row.addWidget(to_lbl)
        to_row.addStretch()
        self.sp_to = QSpinBox()
        self.sp_to.setRange(3, 60)
        self.sp_to.setSuffix(" s")
        self.sp_to.setValue(cfg.get("wake_timeout", 10))
        self.sp_to.valueChanged.connect(
            lambda v: cfg.set_value("wake_timeout", v)
        )
        to_row.addWidget(self.sp_to)
        layout.addLayout(to_row)

        sec3 = QLabel("SENSIBILIDADE")
        sec3.setObjectName("tabSection")
        layout.addWidget(sec3)

        sens_row = QHBoxLayout()
        self.lbl_sens = QLabel(f"{cfg.get('mic_sensitivity', 50)}%")
        self.lbl_sens.setObjectName("fieldLabel")
        self.lbl_sens.setMinimumWidth(40)
        self.sl_sens = QSlider(Qt.Horizontal)
        self.sl_sens.setRange(0, 100)
        self.sl_sens.setValue(cfg.get("mic_sensitivity", 50))
        self.sl_sens.valueChanged.connect(self._on_sens)
        sens_row.addWidget(self.sl_sens)
        sens_row.addWidget(self.lbl_sens)
        layout.addLayout(sens_row)

        hint2 = QLabel("Mais alto = capta sons mais fracos (mais falsos positivos).")
        hint2.setObjectName("fieldHint")
        layout.addWidget(hint2)

        layout.addSpacing(20)
        self.btn_test = QPushButton("TESTAR MICROFONE")
        self.btn_test.setObjectName("configBtn")
        self.btn_test.clicked.connect(self._test_mic)
        layout.addWidget(self.btn_test)

        layout.addStretch()

    def _on_sens(self, v):
        self.lbl_sens.setText(f"{v}%")
        cfg.set_value("mic_sensitivity", v)

    def _test_mic(self):
        print("[MIC] Teste de microfone (TODO no SCRIPT 3)")
