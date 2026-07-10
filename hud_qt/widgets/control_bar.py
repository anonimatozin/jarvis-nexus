"""ControlBar v3 - com botao de captura visual."""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QVBoxLayout
from PySide6.QtCore import Signal, Qt


class ControlBar(QWidget):
    sig_toggle_mic = Signal()
    sig_pause_tts = Signal()
    sig_toggle_capture = Signal()  # NOVO

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlBar")
        self.mic_muted = False
        self.capture_paused = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 20)
        outer.setSpacing(8)

        self.status = QLabel("AGUARDANDO  \u00b7  diga 'Jarvis'")
        self.status.setObjectName("statusLabel")
        self.status.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.status)

        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(20)
        row_layout.addStretch()

        # MIC
        self.btn_mic = QPushButton("\U0001F3A4")
        self.btn_mic.setObjectName("controlBtn")
        self.btn_mic.setToolTip("Silenciar microfone")
        self.btn_mic.clicked.connect(self._on_mic)
        row_layout.addWidget(self.btn_mic)

        # PAUSE TTS
        self.btn_pause = QPushButton("\u23F8")
        self.btn_pause.setObjectName("controlBtn")
        self.btn_pause.setToolTip("Pausar fala atual")
        self.btn_pause.clicked.connect(self.sig_pause_tts.emit)
        row_layout.addWidget(self.btn_pause)

        # CAPTURA VISUAL (NOVO)
        self.btn_capture = QPushButton("\U0001F534")  # 🔴
        self.btn_capture.setObjectName("controlBtn")
        self.btn_capture.setToolTip("Pausar/retomar memoria visual")
        self.btn_capture.clicked.connect(self._on_capture)
        row_layout.addWidget(self.btn_capture)

        row_layout.addStretch()
        outer.addWidget(row)

    def _on_mic(self):
        self.mic_muted = not self.mic_muted
        self.btn_mic.setProperty("muted", "true" if self.mic_muted else "false")
        self.btn_mic.style().unpolish(self.btn_mic)
        self.btn_mic.style().polish(self.btn_mic)
        if self.mic_muted:
            self.set_status("MICROFONE MUTADO")
        else:
            self.set_status("AGUARDANDO  \u00b7  diga 'Jarvis'")
        self.sig_toggle_mic.emit()

    def _on_capture(self):
        self.capture_paused = not self.capture_paused
        # Vermelho quando rodando (gravando), cinza quando pausado
        if self.capture_paused:
            self.btn_capture.setText("\u26AB")  # bola preta
            self.btn_capture.setProperty("muted", "true")
        else:
            self.btn_capture.setText("\U0001F534")  # vermelho
            self.btn_capture.setProperty("muted", "false")
        self.btn_capture.style().unpolish(self.btn_capture)
        self.btn_capture.style().polish(self.btn_capture)
        self.sig_toggle_capture.emit()

    def set_status(self, texto):
        self.status.setText(texto)

    def set_capture_state(self, capturando: bool):
        """Atualiza visual baseado no estado real (chamado pelo engine)."""
        self.capture_paused = not capturando
        if capturando:
            self.btn_capture.setText("\U0001F534")
            self.btn_capture.setProperty("muted", "false")
        else:
            self.btn_capture.setText("\u26AB")
            self.btn_capture.setProperty("muted", "true")
        self.btn_capture.style().unpolish(self.btn_capture)
        self.btn_capture.style().polish(self.btn_capture)
