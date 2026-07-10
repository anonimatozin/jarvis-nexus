"""Aba SOBRE."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt
import os
import subprocess


class TabSobre(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(8)

        title = QLabel("J.A.R.V.I.S.")
        title.setStyleSheet("""
            color: #c8e0f5;
            font-family: 'Segoe UI', sans-serif;
            font-size: 28px;
            font-weight: 600;
            letter-spacing: 8px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("NEXUS v22.0")
        sub.setStyleSheet("""
            color: #5a7a95;
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            letter-spacing: 4px;
        """)
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        desc = QLabel('"Just A Rather Very Intelligent System"')
        desc.setStyleSheet("""
            color: #5a7a95;
            font-family: 'Segoe UI', sans-serif;
            font-size: 10px;
            font-style: italic;
            padding: 16px 0;
        """)
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(10)

        # Stats
        sec = QLabel("ESTATISTICAS DO SISTEMA")
        sec.setObjectName("tabSection")
        layout.addWidget(sec)

        self.lbl_stats = QLabel("Carregando...")
        self.lbl_stats.setObjectName("fieldLabel")
        self.lbl_stats.setWordWrap(True)
        layout.addWidget(self.lbl_stats)
        self._refresh()

        layout.addSpacing(20)

        sec2 = QLabel("ACESSO RAPIDO")
        sec2.setObjectName("tabSection")
        layout.addWidget(sec2)

        btn_logs = QPushButton("ABRIR PASTA DE LOGS")
        btn_logs.setObjectName("configBtn")
        btn_logs.clicked.connect(lambda: self._open("logs"))
        layout.addWidget(btn_logs)

        btn_data = QPushButton("ABRIR PASTA DE DADOS")
        btn_data.setObjectName("configBtn")
        btn_data.clicked.connect(lambda: self._open("data"))
        layout.addWidget(btn_data)

        btn_root = QPushButton("ABRIR PASTA DO JARVIS")
        btn_root.setObjectName("configBtn")
        btn_root.clicked.connect(lambda: self._open("."))
        layout.addWidget(btn_root)

        layout.addStretch()

    def _refresh(self):
        try:
            import psutil
            import os
            proc = psutil.Process(os.getpid())
            ram_mb = proc.memory_info().rss / 1024 / 1024
            cpu = psutil.cpu_percent(interval=0.1)
            txt = f"RAM Jarvis: {ram_mb:.0f} MB\nCPU sistema: {cpu:.0f}%"
            self.lbl_stats.setText(txt)
        except Exception as e:
            self.lbl_stats.setText(f"Erro: {e}")

    def _open(self, sub):
        path = os.path.abspath(sub)
        os.makedirs(path, exist_ok=True)
        try:
            subprocess.Popen(f'explorer "{path}"')
        except:
            pass
