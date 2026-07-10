"""
Controle de luzes Tuya local (sem cloud).
Switches + Lampadas RGB.
"""
import json
import socket
import time
import threading
from pathlib import Path

try:
    import tinytuya
    TUYA_OK = True
except ImportError:
    TUYA_OK = False

CONFIG_PATH = Path("data/luzes.json")


# Cores comuns por nome (RGB)
CORES = {
    "branco": (255, 255, 255),
    "vermelho": (255, 0, 0),
    "verde": (0, 255, 0),
    "azul": (0, 0, 255),
    "amarelo": (255, 255, 0),
    "rosa": (255, 100, 180),
    "roxo": (160, 0, 255),
    "laranja": (255, 100, 0),
    "ciano": (0, 255, 255),
    "magenta": (255, 0, 255),
    "violeta": (130, 0, 200),
}


def carregar_config():
    if not CONFIG_PATH.exists():
        return {"luzes": {}}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except:
        return {"luzes": {}}


def salvar_config(cfg):
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def descobrir_ips():
    """Scan rede e atualiza IPs dos dispositivos."""
    if not TUYA_OK:
        return {}
    print("[LUZ] Scanning rede pra achar IPs...")
    try:
        dispositivos = tinytuya.deviceScan(False, 10)
        ips = {}
        for ip, info in dispositivos.items():
            did = info.get("gwId")
            if did:
                ips[did] = ip
        print(f"[LUZ] {len(ips)} IPs encontrados")
        return ips
    except Exception as e:
        print(f"[LUZ] erro scan: {e}")
        return {}


class LuzesManager:
    def __init__(self, callback_voz=None):
        self.callback_voz = callback_voz
        self.config = carregar_config()
        self._cache_devices = {}  # nome -> device tinytuya
        self._lock = threading.Lock()

        # Tenta descobrir IPs se algum estiver None
        self._verificar_ips()

    def _verificar_ips(self):
        """Se algum IP for None, faz scan."""
        falta_ip = False
        for nome, dados in self.config.get("luzes", {}).items():
            if not dados.get("ip"):
                falta_ip = True
                break
        if falta_ip:
            ips = descobrir_ips()
            for nome, dados in self.config["luzes"].items():
                if not dados.get("ip") and dados["id"] in ips:
                    dados["ip"] = ips[dados["id"]]
                    print(f"[LUZ] {nome} IP descoberto: {dados['ip']}")
            salvar_config(self.config)

    def _get_device(self, nome):
        """Cria/retorna device tinytuya pra essa luz."""
        if not TUYA_OK:
            return None

        with self._lock:
            if nome in self._cache_devices:
                return self._cache_devices[nome]

            dados = self.config["luzes"].get(nome)
            if not dados or not dados.get("ip"):
                return None

            tipo = dados.get("tipo", "switch")

            try:
                if tipo == "bulb_rgb":
                    d = tinytuya.BulbDevice(
                        dev_id=dados["id"],
                        address=dados["ip"],
                        local_key=dados["key"],
                        version=float(dados.get("version", 3.5)),
                    )
                else:
                    d = tinytuya.OutletDevice(
                        dev_id=dados["id"],
                        address=dados["ip"],
                        local_key=dados["key"],
                        version=float(dados.get("version", 3.5)),
                    )
                d.set_socketTimeout(5)
                self._cache_devices[nome] = d
                return d
            except Exception as e:
                print(f"[LUZ] erro criar device {nome}: {e}")
                return None

    def resolver_nome(self, termo):
        """'meu quarto' -> 'quarto'. Retorna nome canonico ou None."""
        if not termo:
            return None
        t = termo.lower().strip()
        for nome, dados in self.config["luzes"].items():
            if t == nome:
                return nome
            for alias in dados.get("aliases", []):
                if alias in t or t in alias:
                    return nome
        return None


    def _cmd_ble(self, tipo, **kwargs):
        """Manda comando pra lampada via ESP32 BLE bridge."""
        try:
            import json as _json
            # Pega referencia do ESP32 manager via engine
            # O engine_callback nao existe aqui, usa arquivo de socket direto
            import socket as _sock
            payload = {"tipo": tipo, **kwargs}
            # Usa WebSocket client simples via TCP
            # ESP32 server ta em ws://192.168.0.109:8766
            # Mas o SERVER ta no PC, ESP32 e o CLIENT
            # Entao mandamos via o server do ESP32 que ja ta no engine
            # Salva em arquivo de fila que o esp32_manager le
            from pathlib import Path as _P
            fila = _P("data/esp32_queue.json")
            fila.parent.mkdir(exist_ok=True)
            import threading
            # Thread-safe append
            import time
            entry = _json.dumps(payload)
            with open(str(fila), "a", encoding="utf-8") as f:
                f.write(entry + "\n")
            return True
        except Exception as e:
            print(f"[LUZ-BLE] erro cmd: {e}")
            return False

    def ligar(self, nome):
        nome = self.resolver_nome(nome)
        if not nome:
            return False, "Luz nao encontrada"
        dados = self.config["luzes"].get(nome, {})
        # Lampada BLE -> via ESP32
        if dados.get("tipo") == "bulb_rgb":
            self._cmd_ble("lamp_on")
            return True, f"Lampada ligada"
        # Switch normal -> tinytuya
        d = self._get_device(nome)
        if not d:
            return False, "Device indisponivel"
        try:
            d.turn_on()
            return True, f"Luz {nome} ligada"
        except Exception as e:
            return False, f"Erro: {e}"
    def desligar(self, nome):
        nome = self.resolver_nome(nome)
        if not nome:
            return False, "Luz nao encontrada"
        dados = self.config["luzes"].get(nome, {})
        if dados.get("tipo") == "bulb_rgb":
            self._cmd_ble("lamp_off")
            return True, f"Lampada desligada"
        d = self._get_device(nome)
        if not d:
            return False, "Device indisponivel"
        try:
            d.turn_off()
            return True, f"Luz {nome} desligada"
        except Exception as e:
            return False, f"Erro: {e}"
    def alternar(self, nome):
        """Toggle - se ligada apaga, se apagada liga."""
        nome = self.resolver_nome(nome)
        if not nome:
            return False, "Luz nao encontrada"
        d = self._get_device(nome)
        if not d:
            return False, "Indisponivel"
        try:
            status = d.status()
            ligada = False
            if isinstance(status, dict):
                dps = status.get("dps", {})
                ligada = dps.get("1", False) or dps.get("20", False)
            if ligada:
                d.turn_off()
                return True, f"Luz {nome} desligada"
            else:
                d.turn_on()
                return True, f"Luz {nome} ligada"
        except Exception as e:
            return False, f"Erro: {e}"

    def cor(self, nome, cor_nome):
        nome = self.resolver_nome(nome)
        if not nome:
            return False, "Luz nao encontrada"
        dados = self.config["luzes"].get(nome, {})
        if dados.get("tipo") == "bulb_rgb":
            self._cmd_ble("lamp_cor", cor=cor_nome.lower().strip())
            return True, f"Cor {cor_nome}"
        return False, f"{nome} nao tem cor"
    def brilho(self, nome, percent):
        nome = self.resolver_nome(nome)
        if not nome:
            return False, "Nao encontrada"
        dados = self.config["luzes"].get(nome, {})
        if dados.get("tipo") == "bulb_rgb":
            v = int(max(0, min(1000, percent * 10)))
            self._cmd_ble("lamp_brilho", valor=v)
            return True, f"Brilho {percent}%"
        d = self._get_device(nome)
        if not d:
            return False, "Indisponivel"
        try:
            v = int(max(10, min(1000, percent * 10)))
            if hasattr(d, "set_brightness"):
                d.set_brightness(v)
            return True, f"Brilho {percent}%"
        except Exception as e:
            return False, f"Erro: {e}"
    def status(self, nome):
        nome = self.resolver_nome(nome)
        if not nome:
            return None
        d = self._get_device(nome)
        if not d:
            return None
        try:
            return d.status()
        except:
            return None

    def listar(self):
        return list(self.config.get("luzes", {}).keys())

    # ═══════ CENAS ═══════
    def cena_dormir(self):
        """Apaga tudo."""
        msgs = []
        for nome in self.listar():
            ok, _ = self.desligar(nome)
            if ok: msgs.append(nome)
        return f"Apagadas: {', '.join(msgs)}" if msgs else "Nada apagou"

    def cena_acordar(self):
        """Liga tudo branco brilhante."""
        msgs = []
        for nome, dados in self.config["luzes"].items():
            ok, _ = self.ligar(nome)
            if ok:
                msgs.append(nome)
                if dados.get("tipo") == "bulb_rgb":
                    time.sleep(0.3)
                    self.cor(nome, "branco")
                    time.sleep(0.2)
                    self.brilho(nome, 100)
        return f"Ligadas: {', '.join(msgs)}"

    def cena_cinema(self):
        """Apaga switches, lampada RGB roxo fraco."""
        for nome, dados in self.config["luzes"].items():
            if dados.get("tipo") == "switch":
                self.desligar(nome)
            elif dados.get("tipo") == "bulb_rgb":
                self.ligar(nome)
                time.sleep(0.3)
                self.cor(nome, "roxo")
                time.sleep(0.2)
                self.brilho(nome, 20)
        return "Modo cinema ativado"

    def cena_iron_man(self):
        """Tudo vermelho/ouro."""
        for nome, dados in self.config["luzes"].items():
            self.ligar(nome)
            time.sleep(0.2)
            if dados.get("tipo") == "bulb_rgb":
                self.cor(nome, "vermelho")
        return "Modo Iron Man, Sir"


_instance = None


def get_luzes(callback_voz=None):
    global _instance
    if _instance is None:
        _instance = LuzesManager(callback_voz=callback_voz)
    return _instance
