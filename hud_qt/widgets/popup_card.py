"""
PopupCard - card lateral que aparece no HUD com informacoes.
Pra clima, pesquisa, imagens, status.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QFrame
)
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QTimer, QEasingCurve, Signal
from PySide6.QtGui import QPixmap, QColor, QFont
import urllib.request
import io


class PopupCard(QFrame):
    """Card popup lateral. Aparece -> fica visivel -> some."""

    sig_fechado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("popupCard")
        self.setFixedWidth(380)
        self.setMinimumHeight(200)
        self.setMaximumHeight(550)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # Header: icone + titulo + X
        header = QHBoxLayout()
        self.lbl_icone = QLabel("🔍")
        self.lbl_icone.setStyleSheet("font-size: 20px;")
        header.addWidget(self.lbl_icone)

        self.lbl_titulo = QLabel("TITULO")
        self.lbl_titulo.setStyleSheet("""
            color: #c8e0f5;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 2px;
        """)
        header.addWidget(self.lbl_titulo, 1)

        self.btn_close = QPushButton("X")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #5a7a95;
                border: none;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #d65a5a;
            }
        """)
        self.btn_close.clicked.connect(self.fechar)
        header.addWidget(self.btn_close)
        layout.addLayout(header)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #2a3340; max-height: 1px;")
        layout.addWidget(sep)

        # Conteudo
        self.lbl_imagem = QLabel()
        self.lbl_imagem.setAlignment(Qt.AlignCenter)
        self.lbl_imagem.setMaximumHeight(150)
        self.lbl_imagem.hide()
        layout.addWidget(self.lbl_imagem)

        self.lbl_texto = QLabel("Conteudo aqui")
        self.lbl_texto.setStyleSheet("""
            color: #8eb5d6;
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            line-height: 1.5;
        """)
        self.lbl_texto.setWordWrap(True)
        layout.addWidget(self.lbl_texto)

        # Lista de links
        self.links_layout = QVBoxLayout()
        layout.addLayout(self.links_layout)

        layout.addStretch()

        # Estilo geral
        self.setStyleSheet("""
            QFrame#popupCard {
                background-color: #141a23;
                border: 1px solid #2a3340;
                border-radius: 10px;
            }
        """)

        # Animacao + timer auto-close
        self._anim = None
        self._timer_close = QTimer()
        self._timer_close.setSingleShot(True)
        self._timer_close.timeout.connect(self.fechar)
        self._is_open = False
        self.hide()

    def mostrar_clima(self, dados):
        """dados: dict do modules.clima"""
        self.lbl_icone.setText("🌤️")
        self.lbl_titulo.setText(dados.get("cidade", "CLIMA").upper()[:20])

        temp = dados.get("temp", "?")
        desc = dados.get("desc", "")
        umid = dados.get("umidade", "?")
        vento = dados.get("vento", "?")

        texto = f"""
        <div style='text-align: center;'>
            <div style='font-size: 48px; color: #c8e0f5; font-weight: 300;'>
                {temp}°C
            </div>
            <div style='font-size: 14px; color: #8eb5d6; margin-top: 8px;'>
                {desc}
            </div>
            <div style='font-size: 11px; color: #5a7a95; margin-top: 12px;'>
                💧 Umidade {umid}% &nbsp;&nbsp; 💨 Vento {vento} km/h
            </div>
        </div>
        """
        self.lbl_texto.setText(texto)
        self.lbl_imagem.hide()
        self._clear_links()

    def mostrar_pesquisa(self, query, resumo, links=None):
        self.lbl_icone.setText("🔍")
        self.lbl_titulo.setText(query.upper()[:25])

        self.lbl_texto.setText(resumo[:400])
        self.lbl_imagem.hide()

        self._clear_links()
        if links:
            for link in links[:3]:
                lbl = QLabel(f"🔗 {link[:50]}")
                lbl.setStyleSheet("""
                    color: #5a7a95;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 10px;
                    padding: 2px 0;
                """)
                lbl.setWordWrap(True)
                self.links_layout.addWidget(lbl)

    def mostrar_imagem(self, titulo, url_imagem):
        self.lbl_icone.setText("🖼️")
        self.lbl_titulo.setText(titulo.upper()[:25])

        try:
            req = urllib.request.Request(url_imagem, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=5).read()
            pix = QPixmap()
            pix.loadFromData(data)
            if not pix.isNull():
                pix = pix.scaled(340, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.lbl_imagem.setPixmap(pix)
                self.lbl_imagem.show()
        except Exception as e:
            self.lbl_texto.setText(f"Erro ao carregar imagem: {e}")

        self._clear_links()

    def mostrar_status(self, cpu, ram, disco):
        self.lbl_icone.setText("💻")
        self.lbl_titulo.setText("STATUS DO PC")
        self.lbl_imagem.hide()

        def bar(valor, max=100):
            preenchido = int((valor / max) * 20)
            return "█" * preenchido + "░" * (20 - preenchido)

        texto = f"""
        <pre style='color: #8eb5d6; font-family: Consolas; font-size: 12px; line-height: 1.6;'>
CPU   {bar(cpu)} {cpu}%
RAM   {bar(ram)} {ram}%
DISCO {bar(disco)} {disco}%
        </pre>
        """
        self.lbl_texto.setText(texto)
        self._clear_links()

    def mostrar_texto(self, titulo, texto, icone="ℹ️"):
        self.lbl_icone.setText(icone)
        self.lbl_titulo.setText(titulo.upper()[:25])
        self.lbl_texto.setText(texto[:500])
        self.lbl_imagem.hide()
        self._clear_links()

    def _clear_links(self):
        while self.links_layout.count():
            item = self.links_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def abrir(self, duracao_ms=15000):
        """Mostra o card animado. Forca HUD aparecer se estiver escondido."""
        parent = self.parent()
        if not parent:
            self.show()
            return

        # NOVO: forca janela principal aparecer se ta escondida
        try:
            main_win = parent.window()
            if main_win and main_win.isHidden():
                # Tenta restaurar via main window
                if hasattr(main_win, "_restore_from_mini"):
                    main_win._restore_from_mini()
                else:
                    main_win.show()
                    main_win.raise_()
        except Exception as e:
            print(f"[POPUP] erro forcar HUD: {e}")

        self.show()
        self.raise_()
        self.adjustSize()

        # Posiciona no canto direito superior, slide-in
        margin = 20
        end_x = parent.width() - self.width() - margin
        end_y = 80
        start_x = parent.width() + 10

        self.setGeometry(start_x, end_y, self.width(), self.height())

        if self._anim:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(400)
        self._anim.setStartValue(QRect(start_x, end_y, self.width(), self.height()))
        self._anim.setEndValue(QRect(end_x, end_y, self.width(), self.height()))
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.start()

        self._is_open = True

        # Auto-close
        if duracao_ms > 0:
            self._timer_close.start(duracao_ms)

    def fechar(self):
        """Slide-out e esconde."""
        if not self._is_open:
            return
        self._timer_close.stop()

        parent = self.parent()
        if not parent:
            self.hide()
            self._is_open = False
            return

        end_x = parent.width() + 10
        start_x = self.x()

        if self._anim:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(300)
        self._anim.setStartValue(QRect(start_x, self.y(), self.width(), self.height()))
        self._anim.setEndValue(QRect(end_x, self.y(), self.width(), self.height()))
        self._anim.setEasingCurve(QEasingCurve.InCubic)
        self._anim.finished.connect(self._on_fechou)
        self._anim.start()

    def _on_fechou(self):
        self.hide()
        self._is_open = False
        self.sig_fechado.emit()

    def reposition(self):
        parent = self.parent()
        if parent and self._is_open:
            margin = 20
            end_x = parent.width() - self.width() - margin
            self.setGeometry(end_x, self.y(), self.width(), self.height())

    def is_open(self):
        return self._is_open

    def estender(self, ms=10000):
        """Reseta timer pra ficar mais tempo aberto."""
        if self._is_open:
            self._timer_close.start(ms)
