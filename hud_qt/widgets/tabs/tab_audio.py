"""Aba AUDIO - saida oficial criptografada."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox,
    QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt


class TabAudio(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(6)

        # ═══ SAIDA OFICIAL ═══
        sec1 = QLabel("SAIDA DE AUDIO OFICIAL")
        sec1.setObjectName("tabSection")
        layout.addWidget(sec1)

        # Dropdown de devices disponiveis (so visivel se nao tem oficial salva)
        self.cb_devices = QComboBox()
        self._popular_devices()
        layout.addWidget(self.cb_devices)

        # Status atual
        self.lbl_atual = QLabel("Carregando...")
        self.lbl_atual.setObjectName("fieldLabel")
        self.lbl_atual.setWordWrap(True)
        layout.addWidget(self.lbl_atual)

        hint = QLabel("Saida fica criptografada (AES-256). So altera por aqui.")
        hint.setObjectName("fieldHint")
        layout.addWidget(hint)

        # Botoes
        btn_salvar = QPushButton("DEFINIR COMO OFICIAL")
        btn_salvar.setObjectName("configBtn")
        btn_salvar.clicked.connect(self._salvar)
        layout.addWidget(btn_salvar)

        btn_testar = QPushButton("TESTAR SAIDA OFICIAL")
        btn_testar.setObjectName("configBtn")
        btn_testar.clicked.connect(self._testar)
        layout.addWidget(btn_testar)

        layout.addSpacing(20)
        sec2 = QLabel("SEGURANCA")
        sec2.setObjectName("tabSection")
        layout.addWidget(sec2)

        info = QLabel(
            "A saida oficial e criptografada com chave derivada do ID do "
            "seu PC. Se copiar a config pra outro computador, nao funciona. "
            "Pra trocar, defina novo device acima."
        )
        info.setObjectName("fieldHint")
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch()
        self._refresh_atual()

    def _popular_devices(self):
        try:
            from audio.output_manager import listar_saidas
            saidas = listar_saidas()
            self.cb_devices.clear()
            if not saidas:
                self.cb_devices.addItem("(nenhum device detectado)")
                return
            for s in saidas:
                self.cb_devices.addItem(f"{s['nome']}")
        except Exception as e:
            print(f"[TAB_AUDIO] erro listar: {e}")

    def _refresh_atual(self):
        try:
            from audio.output_manager import get_oficial_mascarado
            atual = get_oficial_mascarado()
            self.lbl_atual.setText(f"Oficial atual: {atual}")
        except Exception:
            self.lbl_atual.setText("Oficial atual: (erro)")

    def _salvar(self):
        try:
            from audio.output_manager import salvar_oficial
            nome = self.cb_devices.currentText()
            if not nome or "nenhum" in nome.lower():
                QMessageBox.warning(self, "Erro", "Selecione um device.")
                return
            salvar_oficial(nome)
            self._refresh_atual()
            QMessageBox.information(self, "OK",
                "Saida oficial salva (criptografada).")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def _testar(self):
        try:
            from audio.output_manager import testar, get_oficial
            nome = get_oficial()
            if not nome:
                QMessageBox.warning(self, "Erro",
                    "Defina uma saida oficial primeiro.")
                return
            testar(nome)
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))
