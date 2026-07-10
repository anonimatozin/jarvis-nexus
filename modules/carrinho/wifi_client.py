"""
Carrinho - Cliente Wi-Fi (Python -> ESP32)
Envia comandos HTTP simples.
"""

import requests
import time
from . import config as cfg


class WifiClient:
    """Cliente HTTP simples pra ESP32."""

    def __init__(self, ip=None, port=None):
        self.ip = ip or cfg.ESP32_IP
        self.port = port or cfg.ESP32_PORT
        self.base_url = f"http://{self.ip}:{self.port}"
        self.online = False
        self._ultimo_check = 0

    def _url(self, path):
        return f"{self.base_url}/{path.lstrip('/')}"

    def enviar(self, path, params=None):
        """Envia comando GET. Retorna texto ou None."""
        try:
            r = requests.get(
                self._url(path),
                params=params or {},
                timeout=cfg.ESP32_TIMEOUT,
            )
            if r.status_code == 200:
                self.online = True
                return r.text.strip()
            else:
                print(f"[WIFI] HTTP {r.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            self.online = False
            return None
        except requests.exceptions.Timeout:
            print("[WIFI] timeout")
            return None
        except Exception as e:
            print(f"[WIFI] erro: {e}")
            return None

    def ping(self):
        """Testa conexao."""
        r = self.enviar("ping")
        return r is not None

    def status(self):
        """Pega status do ESP32."""
        return self.enviar("status")

    # ════════ MOVIMENTOS BASICOS ════════

    def frente(self, velocidade=None, tempo_ms=None):
        v = velocidade or cfg.VELOCIDADE_PADRAO
        t = tempo_ms or cfg.TEMPO_PADRAO_MS
        return self.enviar("move", {"dir": "F", "v": v, "t": t})

    def tras(self, velocidade=None, tempo_ms=None):
        v = velocidade or cfg.VELOCIDADE_PADRAO
        t = tempo_ms or cfg.TEMPO_PADRAO_MS
        return self.enviar("move", {"dir": "B", "v": v, "t": t})

    def esquerda(self, velocidade=None, tempo_ms=None):
        v = velocidade or cfg.VELOCIDADE_GIRO
        t = tempo_ms or 500
        return self.enviar("move", {"dir": "L", "v": v, "t": t})

    def direita(self, velocidade=None, tempo_ms=None):
        v = velocidade or cfg.VELOCIDADE_GIRO
        t = tempo_ms or 500
        return self.enviar("move", {"dir": "R", "v": v, "t": t})

    def parar(self):
        return self.enviar("stop")

    # ════════ SENSOR HC-SR04 ════════

    def distancia(self, angulo=None):
        """Le distancia em cm. Se passar angulo, gira servo antes."""
        params = {}
        if angulo is not None:
            params["a"] = angulo
        r = self.enviar("dist", params)
        if r:
            try:
                return float(r)
            except:
                return None
        return None

    def varrer(self):
        """Varre servo e retorna distancias em varios angulos."""
        r = self.enviar("scan")
        if r:
            try:
                # Espera formato: "30:120,60:80,90:200,120:50,150:30"
                resultado = {}
                for par in r.split(","):
                    ang, dist = par.split(":")
                    resultado[int(ang)] = float(dist)
                return resultado
            except:
                return None
        return None

    # ════════ SERVO ════════

    def servo(self, angulo):
        """Posiciona servo (0-180)."""
        return self.enviar("servo", {"a": angulo})
