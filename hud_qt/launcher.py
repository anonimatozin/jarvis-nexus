"""HUD Launcher v2 - suporta modo normal + Turbo (ChatGPT)."""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QTimer

from .main_window import JanelaPrincipal


class HudLauncher(QObject):
    """
    USO:
      launcher = HudLauncher(engine_callback=...)
      launcher.create()              # cria QApplication + janela
      launcher.run()                 # bloqueia (event loop Qt)
      launcher.turbo_mode(True)      # entra no modo Turbo
      launcher.turbo_mode(False)     # volta pro modo normal
    """

    def __init__(self, engine_callback=None):
        super().__init__()
        self.engine_callback = engine_callback
        self.window = None
        self.turbo_window = None
        self.app = None
        self._is_turbo = False

    def create(self):
        """Cria QApplication e janela. Chama na MAIN thread."""
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)
        self.window = JanelaPrincipal(engine_callback=self.engine_callback)
        return self.window

    def run(self):
        """Bloqueia no event loop Qt. Chama na MAIN thread."""
        if not self.app:
            self.create()
        self.window.show()
        return self.app.exec()

    def set_orb_state(self, state):
        if self.window and not self._is_turbo:
            self.window.set_orb_state(state)

    def show_from_wake(self):
        if self.window and not self._is_turbo:
            self.window.show_from_wake()

    def show_popup(self, tipo, **kwargs):
        if self.window and not self._is_turbo:
            self.window._show_popup(tipo, **kwargs)

    def show_popup_card(self, **kwargs):
        if self.window and not self._is_turbo:
            self.window._show_popup_card(**kwargs)

    def turbo_mode(self, ativar=True):
        """Troca entre modo normal e Turbo.
        
        Usa QTimer.singleShot(0, ...) para garantir que todas as operacoes
        QWidget rodam na main thread, mesmo quando chamado de threads externas.
        """
        if ativar and not self._is_turbo:
            self._is_turbo = True
            QTimer.singleShot(0, self._abrir_turbo)
        elif not ativar and self._is_turbo:
            self._is_turbo = False
            QTimer.singleShot(0, self._fechar_turbo)

    def _abrir_turbo(self):
        """Abre a janela Turbo na main thread."""
        if self.window:
            self.window.hide()
            self.window.showMinimized()
        from .widgets.turbo_window import TurboWindow
        self.turbo_window = TurboWindow(engine_callback=self.engine_callback)
        self.turbo_window.sig_voltar.connect(self._on_turbo_voltar)
        self.turbo_window.showFullScreen()
        print("[TURBO] Modo Turbo ativo - interface ChatGPT")

    def _fechar_turbo(self):
        """Fecha a janela Turbo e restaura o HUD na main thread."""
        if self.turbo_window:
            self.turbo_window.close()
            self.turbo_window = None
        if self.window:
            self.window.showNormal()
            self.window.activateWindow()
        print("[TURBO] Modo normal restaurado")

    def _on_turbo_voltar(self):
        """Slot para o sinal sig_voltar - chama turbo_mode(False)."""
        self.turbo_mode(False)

    def is_turbo(self):
        return self._is_turbo

    # Compat antigo
    def start(self, blocking=False):
        """DEPRECATED - use create() + run() na main thread."""
        if blocking:
            return self.run()
        else:
            self.create()
