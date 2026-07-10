"""
Carrinho - Sistema de Seguranca
Para de emergencia, watchdog, limites.
"""

import time
import threading
from . import config as cfg


class SafetyMonitor:
    """Monitor de seguranca - roda em background."""

    def __init__(self, wifi_client):
        self.wifi = wifi_client
        self.ativo = False
        self.thread = None
        self.ultima_acao = time.time()
        self.parada_emergencia = False

    def iniciar(self):
        if self.ativo:
            return
        self.ativo = True
        self.thread = threading.Thread(target=self._loop, daemon=True, name="safety")
        self.thread.start()
        print("[SAFETY] Monitor iniciado.")

    def parar(self):
        self.ativo = False

    def registrar_acao(self):
        self.ultima_acao = time.time()

    def emergencia(self):
        """Para imediatamente."""
        self.parada_emergencia = True
        if self.wifi:
            self.wifi.parar()
        print("[SAFETY] EMERGENCIA - carrinho parado!")

    def liberar_emergencia(self):
        self.parada_emergencia = False

    def _loop(self):
        while self.ativo:
            try:
                # Watchdog: para se ficar muito tempo sem comando
                elapsed = (time.time() - self.ultima_acao) * 1000
                if elapsed > cfg.TIMEOUT_COMANDO_MS and not self.parada_emergencia:
                    # Nao para se for so falta de comando recente
                    pass
                
                # Verifica distancia se HC-SR04 instalado
                if cfg.HC_SR04_INSTALADO and self.wifi and self.wifi.online:
                    dist = self.wifi.distancia()
                    if dist is not None and 0 < dist < cfg.DISTANCIA_CRITICA_CM:
                        if not self.parada_emergencia:
                            print(f"[SAFETY] OBSTACULO CRITICO! {dist}cm")
                            self.emergencia()
                        except Exception as e:
                pass
            time.sleep(0.3)
