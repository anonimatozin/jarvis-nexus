"""
JanelaPrincipal v2.3 - clique fora fecha painel + tudo do v2.2.
"""
import sys
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QEvent
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QBrush

from . import config as cfg
from . import styles
from .widgets.orb import Orb
from .widgets.title_bar import TitleBar
from .widgets.control_bar import ControlBar
from .widgets.mini_orb import MiniOrb
from .widgets.config_panel import ConfigPanel
from .widgets.popup_card import PopupCard
from .widgets.popup_notification import PopupNotification


def make_tray_icon():
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QBrush(QColor(cfg.PALETA["orb_listen"])))
    p.setPen(Qt.NoPen)
    p.drawEllipse(12, 12, 40, 40)
    p.setBrush(QBrush(QColor("#ffffff")))
    p.drawEllipse(26, 26, 12, 12)
    p.end()
    return QIcon(pix)


class JanelaPrincipal(QMainWindow):
    sig_state_change = Signal(str)
    sig_show_main = Signal()
    sig_toggle_window = Signal()
    sig_popup = Signal(str, dict)
    sig_camera = Signal(dict)

    def __init__(self, engine_callback=None, parent=None):
        super().__init__(parent)
        self.engine_callback = engine_callback
        self._drag_pos = None
        self._is_maximized = False
        self._normal_geometry = None
        self._last_interaction = time.time()
        self._current_state = "idle"

        self.settings = cfg.load_settings()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setWindowTitle("J.A.R.V.I.S.")
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self._setup_ui()
        self.popup_notif = PopupNotification()
        self._setup_mini_orb()
        self._setup_tray()
        self._setup_idle_timer()
        self._apply_styles()

        self.sig_state_change.connect(self._on_state_change)
        self.sig_show_main.connect(self._show_from_wake)
        self.sig_toggle_window.connect(self._toggle_window_impl)
        self.sig_popup.connect(self._on_popup_signal)
        self.sig_camera.connect(self._on_camera_signal)

        self._setup_hotkey()

        # Filtro global de eventos pra detectar clique fora do painel
        QApplication.instance().installEventFilter(self)

        QTimer.singleShot(100, self._initial_show)

    def eventFilter(self, obj, event):
        """Detecta clique fora do painel pra fecha-lo."""
        try:
            if (event.type() == QEvent.MouseButtonPress
                    and self.config_panel.is_open()):
                # Pega posicao global do mouse
                if hasattr(event, 'globalPosition'):
                    pos = event.globalPosition().toPoint()
                else:
                    pos = event.globalPos()
                # Se clicou fora do painel, fecha
                if not self.config_panel.contains_point(pos):
                    # Mas nao fecha se clicou no botao de config (toggle ja resolve)
                    btn_rect = self.title_bar.btn_config.rect()
                    btn_pos = self.title_bar.btn_config.mapToGlobal(btn_rect.topLeft())
                    btn_global = btn_rect.translated(btn_pos)
                    if not btn_global.contains(pos):
                        self.config_panel.hide_panel()
        except Exception:
            pass
        return super().eventFilter(obj, event)


    @Slot(str, dict)
    def _on_popup_signal(self, tipo, kwargs):
        """Popup independente. CLIMA fecha em 15s. Resto so fecha no X."""
        try:
            notif = self.popup_notif
            if notif is None:
                return

            if tipo == "clima":
                notif.mostrar_clima(kwargs.get("dados", {}))
                notif.abrir(duracao_ms=15000)  # 15 segundos

            elif tipo == "pesquisa":
                notif.mostrar_pesquisa(
                    kwargs.get("query", ""),
                    kwargs.get("resumo", ""),
                    kwargs.get("links", []),
                )
                notif.abrir(duracao_ms=0)  # so X

            elif tipo == "status":
                info = kwargs.get("info", {})
                notif.mostrar_status(
                    info.get("cpu_percent", 0),
                    info.get("ram_used_percent", 0),
                    info.get("disk_used_percent", 0),
                )
                notif.abrir(duracao_ms=0)  # so X

            elif tipo == "imagem":
                notif.mostrar_imagem(
                    kwargs.get("titulo", ""),
                    kwargs.get("url", ""),
                )
                notif.abrir(duracao_ms=0)  # so X

            else:
                notif.mostrar_texto(
                    kwargs.get("titulo", "JARVIS"),
                    kwargs.get("texto", ""),
                    kwargs.get("icone", "ℹ️"),
                )
                notif.abrir(duracao_ms=0)  # so X

            print(f"[POPUP NOTIF] exibido: {tipo}")
        except Exception as ex:
            import traceback
            print(f"[POPUP NOTIF] erro: {ex}")
            traceback.print_exc()

    @Slot(dict)
    def _on_camera_signal(self, dados):
        """Mostra popup de camera via popup_card inline."""
        try:
            notif = self.popup_notif
            if notif is None:
                return
            notif.mostrar_texto(
                dados.get("titulo", "CAMERA"),
                dados.get("texto", "Feed de camera"),
                icone="📷",
            )
            notif.abrir(duracao_ms=0)
        except Exception as ex:
            print(f"[CAMERA POPUP] erro: {ex}")

    
    def show_and_raise(self):
        """Chamado via QMetaObject para mostrar HUD da thread principal."""
        self.show()
        self.raise_()
        self.activateWindow()
        print("[HUD] show_and_raise executado")

    def keyPressEvent(self, event):
        """ESC global tambem fecha painel."""
        if event.key() == Qt.Key_Escape and self.config_panel.is_open():
            self.config_panel.hide_panel()
        else:
            super().keyPressEvent(event)

    def _initial_show(self):
        # Sempre inicia escondido (aparece so no wake word)
        QTimer.singleShot(100, self._minimize_to_orb)

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("mainBackground")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_bar = TitleBar()
        self.title_bar.sig_config.connect(self._on_config)
        self.title_bar.sig_minimize.connect(self._minimize_to_orb)
        self.title_bar.sig_maximize.connect(self._on_maximize)
        self.title_bar.sig_close.connect(self._on_close)
        layout.addWidget(self.title_bar)

        center_wrap = QWidget()
        center_layout = QHBoxLayout(center_wrap)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addStretch()
        self.orb = Orb()
        center_layout.addWidget(self.orb, 1, Qt.AlignCenter)
        center_layout.addStretch()
        layout.addWidget(center_wrap, 1)

        self.control_bar = ControlBar()
        self.control_bar.sig_toggle_mic.connect(self._on_toggle_mic)
        self.control_bar.sig_pause_tts.connect(self._on_pause_tts)
        layout.addWidget(self.control_bar)

        self.config_panel = ConfigPanel(parent=central)
        self.popup_card = PopupCard(parent=central)

    def _setup_mini_orb(self):
        self.mini_orb = MiniOrb()
        self.mini_orb.sig_clicked.connect(self._restore_from_mini)
        self.mini_orb.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        smaller = min(self.width(),
                      self.height() - cfg.TITLE_BAR_HEIGHT - cfg.CONTROL_BAR_HEIGHT)
        orb_size = max(cfg.ORB_MIN_SIZE,
                       min(cfg.ORB_MAX_SIZE, int(smaller * cfg.ORB_DEFAULT_RATIO)))
        self.orb.setMinimumSize(orb_size, orb_size)
        self.orb.setMaximumSize(orb_size + 200, orb_size + 200)
        if hasattr(self, "config_panel"):
            self.config_panel.reposition()

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(make_tray_icon(), self)
        self.tray.setToolTip("J.A.R.V.I.S.")
        menu = QMenu()
        act_show = QAction("Abrir Jarvis", self)
        act_show.triggered.connect(self._restore_from_mini)
        menu.addAction(act_show)
        act_mini = QAction("Modo mini-orb", self)
        act_mini.triggered.connect(self._minimize_to_orb)
        menu.addAction(act_mini)
        menu.addSeparator()
        act_quit = QAction("Encerrar Jarvis", self)
        act_quit.triggered.connect(self._on_close)
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_clicked)
        self.tray.show()

    def _tray_clicked(self, reason):
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.sig_toggle_window.emit()

    def _setup_hotkey(self):
        try:
            import keyboard
            keyboard.add_hotkey("win+j", lambda: self.sig_toggle_window.emit())
            print("[HUD] Atalho Win+J registrado (thread-safe)")
        except Exception as e:
            print(f"[HUD] Atalho falhou: {e}")

    @Slot()
    def _toggle_window_impl(self):
        try:
            if self.isHidden() and self.mini_orb.isHidden():
                self._restore_from_mini()
            elif not self.mini_orb.isHidden():
                self._restore_from_mini()
            else:
                self._minimize_to_orb()
        except Exception as e:
            print(f"[HUD] toggle erro: {e}")

    def _setup_idle_timer(self):
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._check_idle)
        self.idle_timer.start(1000)

    def _check_idle(self):
        if not cfg.get("auto_minimize_idle", True):
            return
        if self.isHidden():
            return
        if self.config_panel.is_open():
            self.reset_idle()
            return
        if self._current_state != "idle":
            self.reset_idle()
            return
        timeout = cfg.get("idle_timeout_seconds", 30)
        if time.time() - self._last_interaction > timeout:
            self._minimize_to_orb()

    def reset_idle(self):
        self._last_interaction = time.time()

    def _apply_styles(self):
        self.setStyleSheet(styles.get_stylesheet())

    def _minimize_to_orb(self):
        try:
            self._save_state()
            if not self._is_maximized:
                self._normal_geometry = self.geometry()
            self.hide()
            self.mini_orb.set_state(self._current_state)
            self.mini_orb.show()
            self.mini_orb.raise_()
        except Exception as e:
            print(f"[HUD] minimize erro: {e}")

    def _restore_from_mini(self):
        try:
            self.mini_orb.hide()
            if self._is_maximized or self._normal_geometry is None:
                self.showMaximized()
                self._is_maximized = True
            else:
                self.showNormal()
                self.setGeometry(self._normal_geometry)
            self.raise_()
            self.activateWindow()
            self.reset_idle()
        except Exception as e:
            print(f"[HUD] restore erro: {e}")

    def _show_from_wake(self):
        if not cfg.get("auto_show_on_wake", True):
            self.reset_idle()
            return
        if not self.mini_orb.isHidden() or self.isHidden():
            self._restore_from_mini()
        self.reset_idle()

    def _on_config(self):
        self.config_panel.toggle()
        self.reset_idle()

    def _on_maximize(self):
        if self._is_maximized:
            self.showNormal()
            self.resize(1000, 700)
            self._center()
            self._is_maximized = False
        else:
            self._normal_geometry = self.geometry()
            self.showMaximized()
            self._is_maximized = True
        self.reset_idle()

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

    def _on_close(self):
        try:
            try:
                import keyboard
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass
            self._save_state()
            self.tray.hide()
            self.mini_orb.hide()
        except Exception:
            pass
        if self.engine_callback:
            try:
                self.engine_callback("__SHUTDOWN__")
            except Exception:
                pass
        QApplication.quit()
        import os
        os._exit(0)

    def _save_state(self):
        try:
            if not self._is_maximized:
                self.settings["ultimo_tamanho"] = [self.width(), self.height()]
                self.settings["ultima_posicao"] = [self.x(), self.y()]
            self.settings["ultimo_estado"] = "fullscreen" if self._is_maximized else "normal"
            cfg.save_settings(self.settings)
        except Exception:
            pass

    def _on_toggle_mic(self):
        cfg.set_value("mic_mutado", self.control_bar.mic_muted)
        self.reset_idle()

    def _on_pause_tts(self):
        self.reset_idle()

    def set_orb_state(self, state):
        self.sig_state_change.emit(state)

    def _on_state_change(self, state):
        self._current_state = state
        self.orb.set_state(state)
        if not self.mini_orb.isHidden():
            self.mini_orb.set_state(state)
        status = {
            "idle": "AGUARDANDO  ·  diga 'Jarvis'",
            "listening": "OUVINDO...",
            "thinking": "PROCESSANDO...",
            "speaking": "RESPONDENDO...",
        }.get(state, "")
        if not self.control_bar.mic_muted:
            self.control_bar.set_status(status)
        if state != "idle":
            self.reset_idle()

    def show_from_wake(self):
        self.sig_show_main.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.position().y() < cfg.TITLE_BAR_HEIGHT:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._drag_pos and not self._is_maximized:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.position().y() < cfg.TITLE_BAR_HEIGHT:
            self._on_maximize()
