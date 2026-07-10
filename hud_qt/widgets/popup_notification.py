"""
PopupNotification v3.0 - Stark Reactor Pro
Notificacoes flutuantes profissionais sem emojis.
"""
import urllib.request
import hashlib
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QApplication, QGridLayout
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QTimer, QEasingCurve,
    Signal, QPoint, QSize
)
from PySide6.QtGui import (
    QPixmap, QColor, QPainter, QBrush, QLinearGradient,
    QPainterPath, QPen, QFont, QIcon
)
from .. import config as cfg

CACHE_DIR = Path("data/popup_images")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

IMAGENS_CLIMA = {
    "ensolarado": "https://images.unsplash.com/photo-1517758478390-c89333af4642?w=600",
    "sol":        "https://images.unsplash.com/photo-1517758478390-c89333af4642?w=600",
    "limpo":      "https://images.unsplash.com/photo-1517758478390-c89333af4642?w=600",
    "nublado":    "https://images.unsplash.com/photo-1500740516770-92bd004b996e?w=600",
    "encoberto":  "https://images.unsplash.com/photo-1500740516770-92bd004b996e?w=600",
    "chuva":      "https://images.unsplash.com/photo-1519692933481-e162a57d6721?w=600",
    "chuvoso":    "https://images.unsplash.com/photo-1519692933481-e162a57d6721?w=600",
    "garoa":      "https://images.unsplash.com/photo-1519692933481-e162a57d6721?w=600",
    "tempestade": "https://images.unsplash.com/photo-1605727216801-e27ce1d0cc28?w=600",
    "trovoada":   "https://images.unsplash.com/photo-1605727216801-e27ce1d0cc28?w=600",
    "neve":       "https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=600",
    "neblina":    "https://images.unsplash.com/photo-1487621167305-5d248087c724?w=600",
}

TRADUCAO_CLIMA = {
    "cloudy": "Nublado", "clear": "Limpo", "sunny": "Ensolarado",
    "rain": "Chuva", "rainy": "Chuvoso", "drizzle": "Garoa",
    "thunderstorm": "Tempestade", "snow": "Neve", "fog": "Neblina",
    "mist": "Neblina", "overcast": "Encoberto",
    "partly cloudy": "Parcialmente nublado",
}

ICONE_MAP = {
    "clima": "\u2601",
    "pesquisa": "\u2315",
    "status": "\u25A6",
    "camera": "\u25A7",
    "imagem": "\u25A3",
    "texto": "\u25C6",
}


def baixar_imagem(url):
    try:
        h = hashlib.md5(url.encode()).hexdigest()[:16]
        cache_path = CACHE_DIR / f"{h}.jpg"
        if cache_path.exists() and cache_path.stat().st_size > 1000:
            return str(cache_path)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=8).read()
        cache_path.write_bytes(data)
        return str(cache_path)
    except Exception:
        return None


def imagem_clima(descricao):
    if not descricao:
        return baixar_imagem(IMAGENS_CLIMA["sol"])
    desc = descricao.lower()
    for chave, url in IMAGENS_CLIMA.items():
        if chave in desc:
            return baixar_imagem(url)
    return baixar_imagem(IMAGENS_CLIMA["sol"])


class PopupNotification(QWidget):
    sig_fechado = Signal()

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(cfg.POPUP_WIDTH, cfg.POPUP_HEIGHT)

        self._bg_pixmap = None
        self._tipo_atual = "texto"
        self._is_open = False

        self._setup_ui()
        self._setup_animacoes()

        self._timer_close = QTimer(self)
        self._timer_close.setSingleShot(True)
        self._timer_close.timeout.connect(self.fechar)

    def _setup_ui(self):
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.container = QWidget(self)
        self.container.setGeometry(0, 0, cfg.POPUP_WIDTH, cfg.POPUP_HEIGHT)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(24, 18, 24, 20)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(12)

        self.lbl_icone = QLabel("\u25C6")
        self.lbl_icone.setFixedSize(32, 32)
        self.lbl_icone.setAlignment(Qt.AlignCenter)
        self.lbl_icone.setStyleSheet(f"""
            background-color: {cfg.PALETA['accent_bg']};
            color: {cfg.PALETA['accent_glow']};
            border: 1px solid {cfg.PALETA['accent_dim']};
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
        """)
        header.addWidget(self.lbl_icone)

        titulo_layout = QVBoxLayout()
        titulo_layout.setSpacing(2)
        self.lbl_titulo = QLabel("JARVIS")
        self.lbl_titulo.setStyleSheet(f"""
            color: {cfg.PALETA['text_bright']};
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 3px;
            background: transparent;
        """)
        titulo_layout.addWidget(self.lbl_titulo)

        self.lbl_subtitulo = QLabel("")
        self.lbl_subtitulo.setStyleSheet(f"""
            color: {cfg.PALETA['text_dim']};
            font-family: 'Segoe UI', sans-serif;
            font-size: 9px;
            letter-spacing: 1px;
            background: transparent;
        """)
        titulo_layout.addWidget(self.lbl_subtitulo)
        header.addLayout(titulo_layout, 1)

        self.btn_close = QPushButton("\u2715")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {cfg.PALETA['text_dim']};
                border: 1px solid transparent;
                border-radius: 12px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {cfg.PALETA['danger']};
                color: white;
                border-color: {cfg.PALETA['danger']};
            }}
        """)
        self.btn_close.clicked.connect(self.fechar)
        header.addWidget(self.btn_close)
        layout.addLayout(header)

        self.sep = QFrame()
        self.sep.setFixedHeight(1)
        self.sep.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.2 {cfg.PALETA['accent_dim']},
                stop:0.8 {cfg.PALETA['accent_dim']}, stop:1 transparent);
        """)
        layout.addWidget(self.sep)

        self.lbl_conteudo = QLabel("")
        self.lbl_conteudo.setAlignment(Qt.AlignCenter)
        self.lbl_conteudo.setWordWrap(True)
        self.lbl_conteudo.setStyleSheet(f"""
            color: {cfg.PALETA['text_bright']};
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            background: transparent;
            line-height: 1.4;
        """)
        layout.addWidget(self.lbl_conteudo, 1)

        self.links_widget = QWidget()
        self.links_widget.setStyleSheet("background: transparent;")
        self.links_layout = QVBoxLayout(self.links_widget)
        self.links_layout.setContentsMargins(0, 0, 0, 0)
        self.links_layout.setSpacing(4)
        layout.addWidget(self.links_widget)

    def _setup_animacoes(self):
        self.anim_slide = QPropertyAnimation(self, b"pos")
        self.anim_slide.setDuration(380)
        self.anim_slide.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_fade = QPropertyAnimation(self, b"windowOpacity")
        self.anim_fade.setDuration(220)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect, 14, 14)
        painter.setClipPath(path)

        painter.fillRect(rect, QColor(6, 9, 15, 240))

        if self._bg_pixmap and not self._bg_pixmap.isNull():
            scaled = self._bg_pixmap.scaled(
                rect.size(), Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            x = (rect.width() - scaled.width()) // 2
            y = (rect.height() - scaled.height()) // 2
            painter.setOpacity(0.35)
            painter.drawPixmap(x, y, scaled)
            painter.setOpacity(1.0)

            grad = QLinearGradient(0, 0, 0, rect.height())
            grad.setColorAt(0, QColor(6, 9, 15, 140))
            grad.setColorAt(0.4, QColor(6, 9, 15, 200))
            grad.setColorAt(1, QColor(6, 9, 15, 240))
            painter.fillRect(rect, QBrush(grad))

        pen = QPen(QColor(42, 127, 255, 100), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 13, 13)

    def _set_icone(self, tipo):
        icone = ICONE_MAP.get(tipo, "\u25C6")
        self.lbl_icone.setText(icone)

    def mostrar_clima(self, dados):
        self._tipo_atual = "clima"
        self._set_icone("clima")

        desc_orig = str(dados.get("desc", ""))
        desc_lower = desc_orig.lower().strip()
        desc = TRADUCAO_CLIMA.get(desc_lower, desc_orig)
        cidade = str(dados.get("cidade", "LOCAL"))[:25].upper()
        temp = dados.get("temp", "?")
        umid = dados.get("umidade", "?")
        vento = dados.get("vento", "?")
        sensacao = dados.get("sensacao", "?")

        self.lbl_titulo.setText(cidade)
        self.lbl_subtitulo.setText("PREVISAO DO TEMPO")

        html = f"""<div style='text-align: center;'>
<div style='font-size: 48px; color: {cfg.PALETA["text_white"]};
    font-weight: 200; letter-spacing: -2px; font-family: Segoe UI;'>
    {temp}<span style='font-size: 28px;'>graus</span>
</div>
<div style='font-size: 13px; color: {cfg.PALETA["text_bright"]};
    margin-top: 4px; letter-spacing: 1px;'>
    {desc}
</div>
<div style='font-size: 11px; color: {cfg.PALETA["text_dim"]};
    margin-top: 14px; letter-spacing: 0.5px;'>
    Sensacao {sensacao}  |  Umidade {umid}%  |  Vento {vento} km/h
</div></div>"""
        self.lbl_conteudo.setText(html)
        self._clear_links()

        img = imagem_clima(desc)
        self._bg_pixmap = QPixmap(img) if img else None
        self.update()

    def mostrar_pesquisa(self, query, resumo, links=None):
        self._tipo_atual = "pesquisa"
        self._set_icone("pesquisa")
        self.lbl_titulo.setText(query.upper()[:30])
        self.lbl_subtitulo.setText("RESULTADO DA PESQUISA")
        self.lbl_conteudo.setText(resumo[:320] if resumo else "Buscando informacoes...")
        self._clear_links()

        if links:
            for link in links[:3]:
                lbl = QLabel(f"  {link[:55]}")
                lbl.setStyleSheet(f"""
                    color: {cfg.PALETA['accent_glow']};
                    font-family: 'Segoe UI'; font-size: 10px;
                    background: transparent; padding: 2px 0;
                """)
                lbl.setWordWrap(True)
                self.links_layout.addWidget(lbl)

        img = baixar_imagem(
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600"
        )
        self._bg_pixmap = QPixmap(img) if img else None
        self.update()

    def mostrar_status(self, cpu, ram, disco):
        self._tipo_atual = "status"
        self._set_icone("status")
        self.lbl_titulo.setText("SISTEMA")
        self.lbl_subtitulo.setText("STATUS DO PC")

        def cor(v):
            if v >= 85: return cfg.PALETA["danger"]
            if v >= 65: return cfg.PALETA["warning"]
            return cfg.PALETA["success"]

        def barra(v):
            p = int((v / 100) * 24)
            preenchido = "\u2588" * p
            vazio = "\u2591" * (24 - p)
            return f"<span style='color:{cor(v)};letter-spacing:1px;'>{preenchido}</span><span style='color:{cfg.PALETA["text_muted"]};'>{vazio}</span>"

        html = f"""<div style='font-family: Consolas, monospace; text-align: left;'>
<div style='margin-bottom: 12px;'>
<span style='color:{cfg.PALETA["text_dim"]}; font-size: 10px; letter-spacing: 2px;'>CPU</span><br>
<span style='font-size: 12px;'>{barra(cpu)}</span>
<span style='color:{cfg.PALETA["text_bright"]}; font-size: 12px; margin-left: 10px;'>{cpu}%</span>
</div>
<div style='margin-bottom: 12px;'>
<span style='color:{cfg.PALETA["text_dim"]}; font-size: 10px; letter-spacing: 2px;'>RAM</span><br>
<span style='font-size: 12px;'>{barra(ram)}</span>
<span style='color:{cfg.PALETA["text_bright"]}; font-size: 12px; margin-left: 10px;'>{ram}%</span>
</div>
<div>
<span style='color:{cfg.PALETA["text_dim"]}; font-size: 10px; letter-spacing: 2px;'>DISCO</span><br>
<span style='font-size: 12px;'>{barra(disco)}</span>
<span style='color:{cfg.PALETA["text_bright"]}; font-size: 12px; margin-left: 10px;'>{disco}%</span>
</div></div>"""
        self.lbl_conteudo.setText(html)
        self.lbl_conteudo.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._clear_links()

        img = baixar_imagem(
            "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600"
        )
        self._bg_pixmap = QPixmap(img) if img else None
        self.update()

    def mostrar_texto(self, titulo, texto, icone=None, manter_aberto=False):
        self._tipo_atual = "texto"
        self._set_icone("texto")
        self.lbl_titulo.setText(titulo.upper()[:30])
        self.lbl_subtitulo.setText("JARVIS")
        self.lbl_conteudo.setText(texto[:420])
        self._clear_links()
        self._bg_pixmap = None
        self.update()

    def mostrar_imagem(self, titulo, url_imagem):
        self._tipo_atual = "imagem"
        self._set_icone("imagem")
        self.lbl_titulo.setText(titulo.upper()[:30])
        self.lbl_subtitulo.setText("VISUALIZACAO")
        self.lbl_conteudo.setText("")
        self._clear_links()
        img = baixar_imagem(url_imagem)
        self._bg_pixmap = QPixmap(img) if img else None
        self.update()

    def _clear_links(self):
        while self.links_layout.count():
            item = self.links_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def abrir(self, duracao_ms=0):
        screen = QApplication.primaryScreen().availableGeometry()
        margin = 24
        end_x = screen.right() - self.width() - margin
        end_y = screen.top() + margin + 12
        start_x = screen.right() + 10

        if self._is_open:
            self._timer_close.stop()
            self._is_open = False

        self.anim_slide.stop()
        self.anim_fade.stop()
        try:
            self.anim_fade.finished.disconnect()
        except (TypeError, RuntimeError):
            pass

        self.move(start_x, end_y)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()
        try:
            import ctypes
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowPos(
                hwnd, -1, 0, 0, 0, 0,
                0x0001 | 0x0002 | 0x0040
            )
        except Exception:
            pass

        self.anim_slide.setStartValue(QPoint(start_x, end_y))
        self.anim_slide.setEndValue(QPoint(end_x, end_y))
        self.anim_slide.start()

        self.anim_fade.setStartValue(0.0)
        self.anim_fade.setEndValue(1.0)
        self.anim_fade.start()

        self._is_open = True

        self._timer_close.stop()
        if duracao_ms and duracao_ms > 0:
            self._timer_close.start(duracao_ms)

    def fechar(self):
        if not self._is_open:
            return
        self._timer_close.stop()

        screen = QApplication.primaryScreen().availableGeometry()
        end_x = screen.right() + 10

        self.anim_slide.stop()
        self.anim_fade.stop()

        try:
            self.anim_fade.finished.disconnect()
        except (TypeError, RuntimeError):
            pass

        self.anim_slide.setStartValue(self.pos())
        self.anim_slide.setEndValue(QPoint(end_x, self.y()))

        self.anim_fade.setStartValue(self.windowOpacity())
        self.anim_fade.setEndValue(0.0)
        self.anim_fade.finished.connect(self._on_fechou)

        self.anim_slide.start()
        self.anim_fade.start()

    def _on_fechou(self):
        self.hide()
        self._is_open = False
        self.sig_fechado.emit()

    def is_open(self):
        return self._is_open

    def fechar_se_auto_voz(self):
        if self._is_open and self._tipo_atual in ("clima", "status"):
            self.fechar()
