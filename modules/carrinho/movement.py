"""
Carrinho - Primitivas de movimento
Wrapper amigavel sobre wifi_client.
"""

import time
from . import config as cfg


class Movement:
    """Movimentos basicos e composicoes."""

    def __init__(self, wifi_client, safety=None):
        self.wifi = wifi_client
        self.safety = safety

    def _acao(self):
        if self.safety:
            self.safety.registrar_acao()

    def frente(self, tempo_ms=None, velocidade=None):
        self._acao()
        return self.wifi.frente(velocidade, tempo_ms)

    def tras(self, tempo_ms=None, velocidade=None):
        self._acao()
        return self.wifi.tras(velocidade, tempo_ms)

    def esquerda(self, tempo_ms=None, velocidade=None):
        self._acao()
        return self.wifi.esquerda(velocidade, tempo_ms)

    def direita(self, tempo_ms=None, velocidade=None):
        self._acao()
        return self.wifi.direita(velocidade, tempo_ms)

    def parar(self):
        self._acao()
        return self.wifi.parar()

    # ════════ COMPOSICOES ════════

    def girar_180(self):
        """Gira 180 graus."""
        self._acao()
        return self.wifi.direita(tempo_ms=1200)

    def dancar(self):
        """Sequencia de demonstracao."""
        self._acao()
        for _ in range(2):
            self.wifi.esquerda(tempo_ms=300)
            time.sleep(0.4)
            self.wifi.direita(tempo_ms=300)
            time.sleep(0.4)
        self.wifi.frente(tempo_ms=500)
        time.sleep(0.6)
        self.wifi.tras(tempo_ms=500)
        time.sleep(0.6)
        self.wifi.parar()

    def quadrado(self):
        """Anda em quadrado."""
        for _ in range(4):
            self.wifi.frente(tempo_ms=1000)
            time.sleep(1.2)
            self.wifi.direita(tempo_ms=600)
            time.sleep(0.8)
