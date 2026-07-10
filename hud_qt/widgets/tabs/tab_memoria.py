"""Aba MEMORIA."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt


class TabMemoria(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(6)

        sec1 = QLabel("ESTATISTICAS")
        sec1.setObjectName("tabSection")
        layout.addWidget(sec1)

        self.lbl_total = QLabel("Carregando...")
        self.lbl_total.setObjectName("fieldLabel")
        layout.addWidget(self.lbl_total)

        self.lbl_cats = QLabel("")
        self.lbl_cats.setObjectName("fieldHint")
        self.lbl_cats.setWordWrap(True)
        layout.addWidget(self.lbl_cats)

        self._refresh_stats()

        sec2 = QLabel("ACOES")
        sec2.setObjectName("tabSection")
        layout.addWidget(sec2)

        btn_refresh = QPushButton("ATUALIZAR ESTATISTICAS")
        btn_refresh.setObjectName("configBtn")
        btn_refresh.clicked.connect(self._refresh_stats)
        layout.addWidget(btn_refresh)

        btn_open = QPushButton("ABRIR PASTA DE MEMORIA")
        btn_open.setObjectName("configBtn")
        btn_open.clicked.connect(self._open_folder)
        layout.addWidget(btn_open)

        layout.addSpacing(20)
        btn_clear = QPushButton("LIMPAR TODAS AS MEMORIAS")
        btn_clear.setObjectName("dangerBtn")
        btn_clear.clicked.connect(self._clear)
        layout.addWidget(btn_clear)

        layout.addStretch()

    def _refresh_stats(self):
        try:
            from memoria.semantic import MemoriaSemantica
            mem = MemoriaSemantica()
            if mem.disponivel:
                s = mem.estatisticas()
                t = s.get("total", 0)
                cats = s.get("categorias", {})
                self.lbl_total.setText(f"Total: {t} lembrancas")
                if cats:
                    txt = "  ·  ".join([f"{k}: {v}" for k, v in cats.items() if v > 0])
                    self.lbl_cats.setText(txt)
                else:
                    self.lbl_cats.setText("Sem categorias.")
            else:
                self.lbl_total.setText("Memoria semantica indisponivel.")
        except Exception as e:
            self.lbl_total.setText(f"Erro: {e}")

    def _open_folder(self):
        import os
        import subprocess
        path = os.path.abspath("data/memoria_semantica")
        os.makedirs(path, exist_ok=True)
        try:
            subprocess.Popen(f'explorer "{path}"')
        except:
            pass

    def _clear(self):
        reply = QMessageBox.question(
            self, "Confirmar",
            "Apagar TODAS as memorias do Jarvis? Esta acao nao pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                from memoria.semantic import MemoriaSemantica
                mem = MemoriaSemantica()
                if mem.disponivel and mem.esquecer():
                    self._refresh_stats()
                    QMessageBox.information(self, "OK", "Memorias apagadas.")
            except Exception as e:
                QMessageBox.warning(self, "Erro", str(e))
