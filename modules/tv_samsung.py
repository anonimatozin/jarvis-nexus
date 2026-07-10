# modules/smartthings.py
"""
J.A.R.V.I.S. - Samsung SmartThings API v1.0
Controle TVs Samsung via SmartThings Cloud.
"""

import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.logger import setup_logger, print_success, print_error, print_system

logger = setup_logger("smartthings")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CONFIG_FILE = DATA_DIR / "tv_config.json"

# SmartThings API
SMARTTHINGS_API = "https://api.smartthings.com/v1"


class SmartThingsAPI:
    """API client para Samsung SmartThings."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("SMARTTHINGS_TOKEN", "")
        self._config = self._carregar_config()
        self._devices_cache = []

        if self.token:
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            self.headers = {}

    def _carregar_config(self) -> Dict:
        try:
            if CONFIG_FILE.exists():
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"tv": {}, "token": ""}

    def _salvar_config(self):
        try:
            CONFIG_FILE.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Erro salvar config: {e}")

    def set_token(self, token: str):
        """Define token de autenticação."""
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self._config["token"] = token
        self._salvar_config()
        print_success("[SMARTTHINGS] Token configurado.")

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Faz request à API."""
        if not self.token:
            return None

        url = f"{SMARTTHINGS_API}{endpoint}"
        try:
            resp = requests.request(
                method, url, headers=self.headers, json=data, timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error(f"SmartThings API error: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            logger.error(f"SmartThings request error: {e}")
            return None

    def listar_devices(self) -> List[Dict]:
        """Lista todos os dispositivos SmartThings."""
        result = self._request("GET", "/devices")
        if result and "items" in result:
            self._devices_cache = result["items"]
            return self._devices_cache
        return []

    def encontrar_tv(self) -> Optional[Dict]:
        """Encontra a TV Samsung nos dispositivos."""
        devices = self.listar_devices()

        for dev in devices:
            # Verifica se é TV Samsung
            if dev.get("manufacturerCode") == "Samsung" or "TV" in dev.get("label", "").upper():
                return dev

            # Verifica capabilities de TV
            caps = [c.get("id", "") for c in dev.get("components", [{}])[0].get("capabilities", [])]
            if any("switch" in c.lower() and "tv" in dev.get("label", "").lower() for c in caps):
                return dev

            # Verifica tipo
            dev_type = dev.get("type", "")
            if dev_type == "TV" or "television" in dev_type.lower():
                return dev

        return None

    def enviar_comando(self, device_id: str, capability: str, command: str, args: Optional[List] = None) -> bool:
        """Envia comando para um dispositivo."""
        data = {
            "commands": [{
                "component": "main",
                "capability": capability,
                "command": command,
                "arguments": args or []
            }]
        }

        result = self._request("POST", f"/devices/{device_id}/commands", data)
        return result is not None


class SmartThingsTV:
    """Controle de TV Samsung via SmartThings."""

    def __init__(self, token: Optional[str] = None):
        self.api = SmartThingsAPI(token)
        self._tv_cache = None
        self._tv_id = None

        # Carrega TV salva
        config = self.api._carregar_config()
        if config.get("tv", {}).get("id"):
            self._tv_id = config["tv"]["id"]

    def _get_tv(self) -> Optional[Dict]:
        """Retorna TV (com cache)."""
        if self._tv_cache:
            return self._tv_cache

        if self._tv_id:
            # Tenta usar ID salvo
            devices = self.api.listar_devices()
            for dev in devices:
                if dev.get("deviceId") == self._tv_id:
                    self._tv_cache = dev
                    return dev

        # Procura TV automaticamente
        tv = self.api.encontrar_tv()
        if tv:
            self._tv_cache = tv
            self._tv_id = tv.get("deviceId")
            # Salva ID
            config = self.api._carregar_config()
            config["tv"] = {
                "id": self._tv_id,
                "nome": tv.get("label", "Samsung TV"),
                "modelo": tv.get("manufacturerCode", "Samsung"),
            }
            self.api._salvar_config()
            print_success(f"[TV] Encontrada: {tv.get('label', 'Samsung TV')}")

        return tv

    def verificar_conexao(self) -> str:
        """Verifica se a TV está conectada."""
        if not self.api.token:
            return "Token SmartThings não configurado. Use: Jarvis configurar SmartThings [token]"

        tv = self._get_tv()
        if tv:
            return f"TV conectada: {tv.get('label', 'Samsung TV')} (ID: {self._tv_id[:8]}...)"

        return "Nenhuma TV Samsung encontrada no SmartThings."

    def _enviar_comando(self, capability: str, command: str, args: Optional[List] = None) -> str:
        """Envia comando para a TV."""
        tv = self._get_tv()
        if not tv:
            return "TV não encontrada. Verifique a conexão."

        device_id = tv.get("deviceId")
        if not device_id:
            return "ID da TV não encontrado."

        ok = self.api.enviar_comando(device_id, capability, command, args)
        if ok:
            return "Comando enviado."
        return "Erro ao enviar comando."

    # ═══ CONTROLES BÁSICOS ═══

    def ligar(self) -> str:
        """Liga a TV."""
        return self._enviar_comando("switch", "on")

    def desligar(self) -> str:
        """Desliga a TV."""
        return self._enviar_comando("switch", "off")

    def alternar(self) -> str:
        """Liga/Desliga TV."""
        return self._enviar_comando("switch", "toggle")

    def volume(self, nivel: Optional[int] = None, direcao: Optional[str] = None) -> str:
        """Controla volume da TV."""
        if nivel is not None:
            return self._enviar_comando("audioVolume", "setVolume", [nivel])
        elif direcao == "up":
            return self._enviar_comando("audioVolume", "volumeUp")
        elif direcao == "down":
            return self._enviar_comando("audioVolume", "volumeDown")
        elif direcao == "mute":
            return self._enviar_comando("audioMute", "setMute", [True])
        elif direcao == "unmute":
            return self._enviar_comando("audioMute", "setMute", [False])
        return self._enviar_comando("audioVolume", "volumeUp")

    def mutar(self) -> str:
        """Muta/Desmuta TV."""
        return self._enviar_comando("audioMute", "toggleMute")

    def canal(self, numero: Optional[int] = None) -> str:
        """Muda canal."""
        if numero is not None:
            return self._enviar_comando("tvChannel", "setTvChannel", [str(numero)])
        return "Número do canal necessário."

    def canal_proximo(self) -> str:
        """Próximo canal."""
        return self._enviar_comando("tvChannel", "channelUp")

    def canal_anterior(self) -> str:
        """Canal anterior."""
        return self._enviar_comando("tvChannel", "channelDown")

    def input(self, fonte: str) -> str:
        """Muda fonte de entrada (HDMI1, HDMI2, TV, etc)."""
        # SmartThings usa Input Source
        return self._enviar_comando("mediaInputSource", "setInputSource", [fonte.lower()])

    def hdmi1(self) -> str:
        """Seleciona HDMI 1."""
        return self.input("HDMI1")

    def hdmi2(self) -> str:
        """Seleciona HDMI 2."""
        return self.input("HDMI2")

    def tv_input(self) -> str:
        """Seleciona entrada TV (antena)."""
        return self.input("TV")

    # ═══ CONTROLES MÍDIA ═══

    def play(self) -> str:
        """Play."""
        return self._enviar_comando("mediaPlayback", "play")

    def pause(self) -> str:
        """Pause."""
        return self._enviar_comando("mediaPlayback", "pause")

    def stop(self) -> str:
        """Stop."""
        return self._enviar_comando("mediaPlayback", "stop")

    def forward(self) -> str:
        """Avançar."""
        return self._enviar_comando("mediaPlayback", "fastForward")

    def rewind(self) -> str:
        """Retroceder."""
        return self._enviar_comando("mediaPlayback", "rewind")

    # ═══ CONTROLES EXTRAS ═══

    def home(self) -> str:
        """Volta pra Home (menu principal)."""
        return self._enviar_comando("tvNavigation", "sendKeyPress", ["KEY_HOME"])

    def back(self) -> str:
        """Volta (back)."""
        return self._enviar_comando("tvNavigation", "sendKeyPress", ["KEY_RETURN"])

    def menu(self) -> str:
        """Abre menu."""
        return self._enviar_comando("tvNavigation", "sendKeyPress", ["KEY_MENU"])

    def seta(self, direcao: str) -> str:
        """Seta direcional (up, down, left, right)."""
        key_map = {
            "up": "KEY_UP",
            "down": "KEY_DOWN",
            "left": "KEY_LEFT",
            "right": "KEY_RIGHT",
            "ok": "KEY_ENTER",
            "enter": "KEY_ENTER",
        }
        key = key_map.get(direcao.lower(), "KEY_ENTER")
        return self._enviar_comando("tvNavigation", "sendKeyPress", [key])

    def confirmar(self) -> str:
        """Pressiona OK/Enter."""
        return self.seta("ok")

    # ═══ STATUS ═══

    def status(self) -> str:
        """Status da TV."""
        tv = self._get_tv()
        if not tv:
            return "TV não encontrada."

        status_parts = [f"TV: {tv.get('label', 'Samsung TV')}"]

        # Pega estado do switch
        try:
            components = tv.get("components", [])
            if components:
                main = components[0]
                caps = main.get("capabilities", [])
                for cap in caps:
                    if cap.get("id") == "switch":
                        status_parts.append("Status: Online")
                        break
        except Exception:
            pass

        return " | ".join(status_parts)

    def listar_fontes(self) -> str:
        """Lista fontes de entrada disponíveis."""
        return "Fontes: HDMI1, HDMI2, HDMI3, TV, AV, Component"

    def listar_canais(self) -> str:
        """Lista canais salvos (placeholder)."""
        return "Canais: Use 'Jarvis canal [número]' para mudar."


# ═══ SINGLETON ═══

_tv_instance = None

def get_tv(token: Optional[str] = None):
    global _tv_instance
    if _tv_instance is None:
        _tv_instance = SmartThingsTV(token)
    return _tv_instance
