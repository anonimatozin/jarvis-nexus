"""Aba IA - so provider, sem temperatura."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout
)
from PySide6.QtCore import Qt

from ... import config as cfg


class TabIA(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(6)

        sec1 = QLabel("PROVIDER PREFERIDO")
        sec1.setObjectName("tabSection")
        layout.addWidget(sec1)

        self.cb_prov = QComboBox()
        self.cb_prov.addItems([
            "Auto (cascata)",
            "Gemini (Google - 1500/dia)",
            "Groq (Llama 3.3 - rapido)",
            "Ollama (offline)",
        ])
        atual = cfg.get("ai_provider", "auto")
        map_idx = {"auto": 0, "gemini": 1, "groq": 2, "ollama": 3}
        self.cb_prov.setCurrentIndex(map_idx.get(atual, 0))
        self.cb_prov.currentIndexChanged.connect(self._on_prov)
        layout.addWidget(self.cb_prov)

        hint = QLabel("Auto: tenta Gemini -> Groq -> Ollama em cascata.")
        hint.setObjectName("fieldHint")
        layout.addWidget(hint)

        sec3 = QLabel("STATUS DOS PROVIDERS")
        sec3.setObjectName("tabSection")
        layout.addWidget(sec3)

        self._add_status(layout, "Gemini",  self._check_gemini())
        self._add_status(layout, "Groq",    self._check_groq())
        self._add_status(layout, "Ollama",  self._check_ollama())

        layout.addStretch()

    def _add_status(self, layout, nome, ok):
        row = QHBoxLayout()
        lbl = QLabel(nome)
        lbl.setObjectName("fieldLabel")
        row.addWidget(lbl)
        row.addStretch()
        status = QLabel("● ONLINE" if ok else "○ OFFLINE")
        status.setStyleSheet(
            f"color: {'#5ad68e' if ok else '#5a7a95'}; font-size: 11px;"
        )
        row.addWidget(status)
        layout.addLayout(row)

    def _check_gemini(self):
        import os
        return bool(os.getenv("GEMINI_API_KEY", "").strip())

    def _check_groq(self):
        import os
        return bool(os.getenv("GROQ_API_KEY", "").strip())

    def _check_ollama(self):
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=1)
            return r.status_code == 200
        except:
            return False

    def _on_prov(self, idx):
        map_val = {0: "auto", 1: "gemini", 2: "groq", 3: "ollama"}
        cfg.set_value("ai_provider", map_val.get(idx, "auto"))
