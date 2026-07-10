"""Aba VOZ - Configuracoes TTS."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSlider, QComboBox,
    QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt

from ... import config as cfg


class TabVoz(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(6)

        sec1 = QLabel("VOLUME")
        sec1.setObjectName("tabSection")
        layout.addWidget(sec1)

        vol_row = QHBoxLayout()
        self.lbl_vol = QLabel(f"{cfg.get('tts_volume', 80)}%")
        self.lbl_vol.setObjectName("fieldLabel")
        self.lbl_vol.setMinimumWidth(40)
        self.sl_vol = QSlider(Qt.Horizontal)
        self.sl_vol.setRange(0, 100)
        self.sl_vol.setValue(cfg.get("tts_volume", 80))
        self.sl_vol.valueChanged.connect(self._on_vol)
        vol_row.addWidget(self.sl_vol)
        vol_row.addWidget(self.lbl_vol)
        layout.addLayout(vol_row)

        sec2 = QLabel("VOZ")
        sec2.setObjectName("tabSection")
        layout.addWidget(sec2)

        self.cb_voice = QComboBox()
        self.cb_voice.addItems([
            "pt-BR-AntonioNeural (Masculina BR)",
            "pt-BR-FranciscaNeural (Feminina BR)",
            "pt-BR-ThalitaNeural (Feminina BR jovem)",
            "pt-PT-DuarteNeural (Masculina PT)",
            "en-US-GuyNeural (Masculina US)",
        ])
        atual = cfg.get("tts_voice", "pt-BR-AntonioNeural")
        for i in range(self.cb_voice.count()):
            if atual in self.cb_voice.itemText(i):
                self.cb_voice.setCurrentIndex(i)
                break
        self.cb_voice.currentTextChanged.connect(self._on_voice)
        layout.addWidget(self.cb_voice)

        sec3 = QLabel("VELOCIDADE")
        sec3.setObjectName("tabSection")
        layout.addWidget(sec3)

        speed_row = QHBoxLayout()
        self.lbl_speed = QLabel(f"{cfg.get('tts_speed', 1.0):.1f}x")
        self.lbl_speed.setObjectName("fieldLabel")
        self.lbl_speed.setMinimumWidth(40)
        self.sl_speed = QSlider(Qt.Horizontal)
        self.sl_speed.setRange(5, 20)  # 0.5 a 2.0 (x10)
        self.sl_speed.setValue(int(cfg.get("tts_speed", 1.0) * 10))
        self.sl_speed.valueChanged.connect(self._on_speed)
        speed_row.addWidget(self.sl_speed)
        speed_row.addWidget(self.lbl_speed)
        layout.addLayout(speed_row)

        layout.addSpacing(20)
        self.btn_test = QPushButton("TESTAR VOZ")
        self.btn_test.setObjectName("configBtn")
        self.btn_test.clicked.connect(self._test_voice)
        layout.addWidget(self.btn_test)

        layout.addStretch()

    def _on_vol(self, v):
        self.lbl_vol.setText(f"{v}%")
        cfg.set_value("tts_volume", v)

    def _on_voice(self, txt):
        name = txt.split(" (")[0]
        cfg.set_value("tts_voice", name)

    def _on_speed(self, v):
        speed = v / 10.0
        self.lbl_speed.setText(f"{speed:.1f}x")
        cfg.set_value("tts_speed", speed)

    def _test_voice(self):
        try:
            from output.tts_engine import TTSEngine
            import threading
            def speak():
                tts = TTSEngine()
                tts.speak("Testando voz, Sir. Sistema operacional.")
            threading.Thread(target=speak, daemon=True).start()
        except Exception as e:
            print(f"[VOZ] teste falhou: {e}")
