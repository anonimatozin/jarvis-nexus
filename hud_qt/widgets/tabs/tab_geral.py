"""Aba GERAL - Comportamento da janela."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox, QSpinBox, QHBoxLayout
)
from PySide6.QtCore import Qt

from ... import config as cfg

try:
    from scripts.windows_startup import is_startup_enabled, set_startup
    STARTUP_OK = True
except ImportError:
    STARTUP_OK = False


class TabGeral(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(6)

        # ═══ SECAO: INICIALIZACAO ═══
        sec1 = QLabel("INICIALIZACAO")
        sec1.setObjectName("tabSection")
        layout.addWidget(sec1)

        self.cb_startup = QCheckBox("Iniciar com o Windows")
        # Detecta estado real do registro
        if STARTUP_OK:
            real_state = is_startup_enabled()
        else:
            real_state = cfg.get("iniciar_com_windows", False)
        self.cb_startup.setChecked(real_state)
        self.cb_startup.toggled.connect(self._on_startup)
        layout.addWidget(self.cb_startup)

        hint1 = QLabel("Cria atalho no boot do Windows. Aplicado imediatamente.")
        hint1.setObjectName("fieldHint")
        layout.addWidget(hint1)

        self.cb_min_start = QCheckBox("Iniciar minimizado (mini-orb)")
        self.cb_min_start.setChecked(cfg.get("iniciar_minimizado", False))
        self.cb_min_start.toggled.connect(
            lambda v: cfg.set_value("iniciar_minimizado", v)
        )
        layout.addWidget(self.cb_min_start)

        # ═══ SECAO: AUTO-MINIMIZE ═══
        sec2 = QLabel("AUTO-MINIMIZE")
        sec2.setObjectName("tabSection")
        layout.addWidget(sec2)

        self.cb_auto_min = QCheckBox("Minimizar automaticamente quando ocioso")
        self.cb_auto_min.setChecked(cfg.get("auto_minimize_idle", True))
        self.cb_auto_min.toggled.connect(
            lambda v: cfg.set_value("auto_minimize_idle", v)
        )
        layout.addWidget(self.cb_auto_min)

        timeout_row = QHBoxLayout()
        timeout_row.setContentsMargins(0, 4, 0, 4)
        timeout_lbl = QLabel("Tempo de inatividade:")
        timeout_lbl.setObjectName("fieldLabel")
        timeout_row.addWidget(timeout_lbl)
        timeout_row.addStretch()
        self.sp_timeout = QSpinBox()
        self.sp_timeout.setRange(5, 600)
        self.sp_timeout.setSingleStep(5)
        self.sp_timeout.setSuffix(" segundos")
        self.sp_timeout.setValue(cfg.get("idle_timeout_seconds", 30))
        self.sp_timeout.valueChanged.connect(
            lambda v: cfg.set_value("idle_timeout_seconds", v)
        )
        timeout_row.addWidget(self.sp_timeout)
        layout.addLayout(timeout_row)

        # ═══ SECAO: WAKE WORD ═══
        sec3 = QLabel("WAKE WORD")
        sec3.setObjectName("tabSection")
        layout.addWidget(sec3)

        self.cb_auto_show = QCheckBox("Abrir HUD ao dizer 'Jarvis'")
        self.cb_auto_show.setChecked(cfg.get("auto_show_on_wake", True))
        self.cb_auto_show.toggled.connect(
            lambda v: cfg.set_value("auto_show_on_wake", v)
        )
        layout.addWidget(self.cb_auto_show)

        hint3 = QLabel("Quando minimizado, abre fullscreen automaticamente.")
        hint3.setObjectName("fieldHint")
        layout.addWidget(hint3)

        layout.addStretch()

    def _on_startup(self, checked):
        """Liga/desliga inicio com Windows."""
        cfg.set_value("iniciar_com_windows", checked)
        if STARTUP_OK:
            try:
                ok = set_startup(checked)
                if not ok:
                    print("[CONFIG] erro ao mexer no registro do Windows")
            except Exception as e:
                print(f"[CONFIG] startup falhou: {e}")
