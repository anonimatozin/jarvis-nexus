"""
TurboWindow v2.0 - Interface estilo ChatGPT para modo Turbo.
Fix: thread deadlock, timeout, UI stability.
"""
import os
import re
import time
import traceback
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QScrollArea,
    QFrame, QLabel, QFileDialog, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize, QMutex, QMutexLocker
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QTextCursor

from .. import config as cfg


class _WorkerThread(QThread):
    """Thread separada pra enviar mensagem sem bloquear UI."""
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, engine_callback, texto, anexos=None):
        super().__init__()
        self.engine_callback = engine_callback
        self.texto = texto
        self.anexos = anexos
        self._cancelado = False

    def run(self):
        try:
            if self._cancelado:
                return
            if self.engine_callback:
                contexto = self.texto
                if self.anexos:
                    nomes = [Path(a).name for a in self.anexos]
                    contexto += f"\n[Anexos: {', '.join(nomes)}]"
                resultado = self.engine_callback(contexto)
                if not self._cancelado:
                    self.finished.emit(str(resultado) if resultado else "Sem resposta.")
            else:
                if not self._cancelado:
                    self.finished.emit("Engine offline.")
        except Exception as e:
            if not self._cancelado:
                self.error.emit(f"Erro: {e}")

    def cancelar(self):
        self._cancelado = True


class ChatBubble(QFrame):
    """Balao de mensagem individual."""

    def __init__(self, texto, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self._setup_ui(texto)

    def _setup_ui(self, texto):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)

        bubble = QFrame()
        bubble.setMaximumWidth(700)

        bbl = QVBoxLayout(bubble)
        bbl.setContentsMargins(14, 10, 14, 10)
        bbl.setSpacing(4)

        sender = QLabel("Voce" if self.is_user else "Jarvis")
        sender.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        sender.setStyleSheet(f"color: {cfg.PALETA['accent_glow'] if self.is_user else cfg.PALETA['text_bright']}; background: transparent; border: none;")
        bbl.addWidget(sender)

        lbl = QLabel(texto)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setFont(QFont("Segoe UI", 11))
        lbl.setStyleSheet(f"color: {cfg.PALETA['text_white']}; background: transparent; border: none; line-height: 1.5;")
        bbl.addWidget(lbl)

        if self.is_user:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {cfg.PALETA['accent_bg']};
                    border: 1px solid {cfg.PALETA['accent_dim']};
                    border-radius: 12px;
                }}
            """)
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {cfg.PALETA['bg_card']};
                    border: 1px solid {cfg.PALETA['border']};
                    border-radius: 12px;
                }}
            """)
            layout.addWidget(bubble)
            layout.addStretch()


class TurboWindow(QMainWindow):
    """Janela principal do Turbo Mode - estilo ChatGPT."""

    sig_voltar = Signal()

    def __init__(self, engine_callback=None, parent=None):
        super().__init__(parent)
        self.engine_callback = engine_callback
        self.anexos = []
        self._worker = None
        self._enviando = False
        self._bubbles = []  # referencia pras bolhas

        self.setWindowTitle("J.A.R.V.I.S. TURBO")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)

        self._setup_ui()
        self._apply_styles()

        self.sig_voltar.connect(self._voltar)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ═══ HEADER ═══
        header = QFrame()
        header.setFixedHeight(52)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("J.A.R.V.I.S. TURBO")
        title.setFont(QFont("Consolas", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {cfg.PALETA['accent_glow']}; letter-spacing: 3px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        subtitle = QLabel("Modo Avancado")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet(f"color: {cfg.PALETA['text_dim']};")
        header_layout.addWidget(subtitle)

        btn_close = QPushButton("\u2715")
        btn_close.setFixedSize(36, 36)
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(lambda: self.sig_voltar.emit())
        header_layout.addWidget(btn_close)

        main_layout.addWidget(header)

        # Separador
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 transparent, stop:0.2 {cfg.PALETA['accent_dim']}, stop:0.8 {cfg.PALETA['accent_dim']}, stop:1 transparent);")
        main_layout.addWidget(sep)

        # ═══ AREA DE CHAT ═══
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {cfg.PALETA['bg_main']};
                border: none;
            }}
            QScrollBar:vertical {{
                width: 6px;
                background: {cfg.PALETA['bg_main']};
            }}
            QScrollBar::handle:vertical {{
                background: {cfg.PALETA['border']};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {cfg.PALETA['accent_dim']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_layout.setSpacing(8)

        self.chat_scroll.setWidget(self.chat_container)
        main_layout.addWidget(self.chat_scroll, 1)

        # ═══ AREA DE ANEXOS ═══
        self.anexos_frame = QFrame()
        self.anexos_frame.setFixedHeight(50)
        self.anexos_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {cfg.PALETA['bg_panel']};
                border-top: 1px solid {cfg.PALETA['border']};
            }}
        """)
        anexos_layout = QHBoxLayout(self.anexos_frame)
        anexos_layout.setContentsMargins(16, 6, 16, 6)

        self.lbl_anexos = QLabel("")
        self.lbl_anexos.setFont(QFont("Segoe UI", 10))
        self.lbl_anexos.setStyleSheet(f"color: {cfg.PALETA['text_dim']}; background: transparent;")
        anexos_layout.addWidget(self.lbl_anexos)
        anexos_layout.addStretch()

        self.anexos_frame.setVisible(False)
        main_layout.addWidget(self.anexos_frame)

        # Separador
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {cfg.PALETA['border']};")
        main_layout.addWidget(sep2)

        # ═══ INPUT AREA ═══
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {cfg.PALETA['bg_panel']};
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)

        self.btn_anexar = QPushButton("\u2295")
        self.btn_anexar.setFixedSize(40, 40)
        self.btn_anexar.setCursor(Qt.PointingHandCursor)
        self.btn_anexar.setToolTip("Anexar arquivo ou imagem")
        self.btn_anexar.clicked.connect(self._anexar_arquivo)
        input_layout.addWidget(self.btn_anexar)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Digite sua mensagem...")
        self.input_field.setFont(QFont("Segoe UI", 12))
        self.input_field.returnPressed.connect(self._enviar)
        input_layout.addWidget(self.input_field, 1)

        self.btnEnviar = QPushButton("\u25B6")
        self.btnEnviar.setFixedSize(40, 40)
        self.btnEnviar.setCursor(Qt.PointingHandCursor)
        self.btnEnviar.clicked.connect(self._enviar)
        input_layout.addWidget(self.btnEnviar)

        main_layout.addWidget(input_frame)

        # Mensagem de boas-vindas
        self._adicionar_mensagem(
            "Modo Turbo ativo. Pode mandar arquivos, imagens, planilhas ou qualquer coisa. "
            "Eu analiso e respondo em tempo real.",
            is_user=False
        )

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {cfg.PALETA['bg_main']};
            }}
            QLineEdit {{
                background-color: {cfg.PALETA['bg_elevated']};
                color: {cfg.PALETA['text_white']};
                border: 1px solid {cfg.PALETA['border']};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {cfg.PALETA['accent']};
            }}
            QPushButton {{
                background-color: {cfg.PALETA['accent']};
                color: {cfg.PALETA['text_white']};
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {cfg.PALETA['accent_glow']};
            }}
            QPushButton:pressed {{
                background-color: {cfg.PALETA['accent_dim']};
            }}
        """)

        self.btn_anexar.setStyleSheet(f"""
            QPushButton {{
                background-color: {cfg.PALETA['bg_elevated']};
                color: {cfg.PALETA['text_dim']};
                border: 1px solid {cfg.PALETA['border']};
                border-radius: 8px;
                font-size: 20px;
            }}
            QPushButton:hover {{
                border-color: {cfg.PALETA['accent']};
                color: {cfg.PALETA['accent_glow']};
            }}
        """)

        for btn in self.findChildren(QPushButton):
            if btn.text() == "\u2715":
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {cfg.PALETA['text_dim']};
                        border: none;
                        font-size: 16px;
                    }}
                    QPushButton:hover {{
                        color: {cfg.PALETA['danger']};
                    }}
                """)

    def _adicionar_mensagem(self, texto, is_user=True):
        """Adiciona um balao de chat na area de scroll."""
        bubble = ChatBubble(texto, is_user=is_user)
        self._bubbles.append(bubble)
        self.chat_layout.addWidget(bubble)

        # Rola pro final com delay
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _remover_ultima_mensagem(self):
        """Remove a ultima mensagem adicionada."""
        if self._bubbles:
            ultima = self._bubbles.pop()
            self.chat_layout.removeWidget(ultima)
            ultima.deleteLater()

    def _scroll_to_bottom(self):
        try:
            sb = self.chat_scroll.verticalScrollBar()
            sb.setValue(sb.maximum())
        except Exception:
            pass

    def _anexar_arquivo(self):
        caminhos, _ = QFileDialog.getOpenFileNames(
            self, "Anexar arquivos",
            str(Path.home() / "Desktop"),
            "Todos os arquivos (*);;Imagens (*.png *.jpg *.jpeg *.bmp *.gif);;"
            "Planilhas (*.xlsx *.xls *.csv);;Texto (*.txt *.md *.py *.json)"
        )
        if caminhos:
            for c in caminhos:
                if c not in self.anexos:
                    self.anexos.append(c)
            self._atualizar_anexos()

    def _atualizar_anexos(self):
        if not self.anexos:
            self.anexos_frame.setVisible(False)
            return
        self.anexos_frame.setVisible(True)
        nomes = [Path(a).name for a in self.anexos[-5:]]
        txt = "Anexos: " + ", ".join(nomes)
        if len(self.anexos) > 5:
            txt += f" (+{len(self.anexos) - 5} mais)"
        self.lbl_anexos.setText(txt)

    def _enviar(self):
        """Envia mensagem do usuario."""
        if self._enviando:
            return  # ja esta processando

        texto = self.input_field.text().strip()
        if not texto and not self.anexos:
            return

        msg = texto
        if self.anexos:
            nomes = [Path(a).name for a in self.anexos]
            msg += f"\n[Anexos: {', '.join(nomes)}]"

        self._adicionar_mensagem(msg, is_user=True)
        self.input_field.clear()

        anexos_copy = list(self.anexos)
        self.anexos.clear()
        self._atualizar_anexos()

        # Mostra "digitando..."
        self._adicionar_mensagem("...", is_user=False)
        self._enviando = True
        self.btnEnviar.setEnabled(False)
        self.input_field.setEnabled(False)

        # Worker com timeout
        self._worker = _WorkerThread(self.engine_callback, texto, anexos_copy)
        self._worker.finished.connect(self._on_resposta)
        self._worker.error.connect(self._on_erro)
        self._worker.finished.connect(self._liberar_envio)
        self._worker.error.connect(self._liberar_envio)
        self._worker.start()

        # Timeout de 60 segundos
        QTimer.singleShot(60000, self._timeout_check)

    def _timeout_check(self):
        """Verifica se worker travou."""
        if self._enviando and self._worker and self._worker.isRunning():
            self._worker.cancelar()
            self._remover_ultima_mensagem()  # remove "..."
            self._adicionar_mensagem(
                "Tempo limite atingido. Tente algo mais simples ou verifique a engine.",
                is_user=False
            )
            self._liberar_envio()

    def _liberar_envio(self):
        """Libera o estado de envio."""
        self._enviando = False
        self.btnEnviar.setEnabled(True)
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

    def _on_resposta(self, texto):
        """Recebe resposta da engine."""
        self._remover_ultima_mensagem()  # remove "..."
        self._adicionar_mensagem(texto, is_user=False)

    def _on_erro(self, texto):
        """Recebe erro da engine."""
        self._remover_ultima_mensagem()  # remove "..."
        self._adicionar_mensagem(texto, is_user=False)

    def _voltar(self):
        # Cancela worker se ativo
        if self._worker and self._worker.isRunning():
            self._worker.cancelar()
        # NAO re-emite sig_voltar - o launcher já trata via conexão

    def closeEvent(self, event):
        """Cleanup ao fechar - nao bloqueia event loop."""
        if self._worker and self._worker.isRunning():
            self._worker.cancelar()
        # Desconecte sinais antes de destruir
        try:
            self.sig_voltar.disconnect()
        except RuntimeError:
            pass
        if self._worker:
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except RuntimeError:
                pass
        super().closeEvent(event)

    def _enviar_comando(self, texto):
        self.input_field.setText(texto)
        self._enviar()
