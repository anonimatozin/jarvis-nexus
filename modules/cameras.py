"""
Cameras IP (Yoosee/ONVIF).
Scanner + stream + config persistente.
"""
import json
import socket
import threading
import time
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

CONFIG_PATH = Path("data/cameras.json")
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Portas tipicas de cameras
PORTAS_RTSP = [554]
PORTAS_YOOSEE = [554, 8800, 5000]


def porta_aberta(ip, porta, timeout=0.5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((ip, porta)) == 0
    except:
        return False
    finally:
        s.close()


def carregar_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except:
            pass
    return {
        "usuario_padrao": "admin",
        "senha_padrao": "",
        "cameras": {},  # nome -> {ip, user, pass, rtsp_url}
    }


def salvar_config(cfg):
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def scan_rede_cameras(faixa="192.168.0", callback_progresso=None):
    """Varre rede procurando IPs com porta 554 (RTSP) aberta."""
    encontradas = []

    def checar_ip(i):
        ip = f"{faixa}.{i}"
        if porta_aberta(ip, 554, timeout=0.4):
            # Verifica se eh Yoosee (porta 8800 tambem)
            tipo = "rtsp"
            if porta_aberta(ip, 8800, timeout=0.3):
                tipo = "yoosee"
            return {"ip": ip, "tipo": tipo}
        return None

    with ThreadPoolExecutor(max_workers=50) as exe:
        futuros = [exe.submit(checar_ip, i) for i in range(1, 255)]
        completas = 0
        for f in futuros:
            r = f.result()
            completas += 1
            if callback_progresso and completas % 30 == 0:
                callback_progresso(completas)
            if r:
                encontradas.append(r)

    return encontradas


def testar_rtsp_url(url, timeout=5):
    """Tenta abrir RTSP e ler 1 frame pra confirmar que funciona."""
    try:
        import cv2
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
        ret, _ = cap.read()
        cap.release()
        return ret
    except Exception as e:
        print(f"[CAM] erro testar {url}: {e}")
        return False


def descobrir_url_yoosee(ip, user="admin", senha=""):
    """Testa URLs comuns Yoosee/ONVIF e retorna a que funciona."""
    URLS_POSSIVEIS = [
        f"rtsp://{user}:{senha}@{ip}:554/onvif1",
        f"rtsp://{user}:{senha}@{ip}:554/onvif2",
        f"rtsp://{user}:{senha}@{ip}:554/11",
        f"rtsp://{user}:{senha}@{ip}:554/12",
        f"rtsp://{user}:{senha}@{ip}:554/live/ch0",
        f"rtsp://{user}:{senha}@{ip}:554/live/ch1",
        f"rtsp://{user}:{senha}@{ip}:554/cam/realmonitor?channel=1&subtype=0",
        f"rtsp://{user}:{senha}@{ip}:554/h264Preview_01_main",
        f"rtsp://{user}:{senha}@{ip}:554/h264Preview_01_sub",
    ]

    for url in URLS_POSSIVEIS:
        print(f"[CAM] Testando: {url}")
        if testar_rtsp_url(url, timeout=4):
            print(f"[CAM] ✓ OK: {url}")
            return url

    return None


class CamerasManager:
    def __init__(self, callback_voz=None, callback_popup=None):
        self.callback_voz = callback_voz
        self.callback_popup = callback_popup  # pra abrir popup video
        self.config = carregar_config()

    def listar(self):
        return self.config.get("cameras", {})

    def adicionar_camera(self, nome, ip, user="admin", senha=""):
        """Adiciona manualmente."""
        url = descobrir_url_yoosee(ip, user, senha)
        if not url:
            return False, f"Nao consegui conectar em {ip}"
        self.config["cameras"][nome.lower()] = {
            "ip": ip,
            "user": user,
            "senha": senha,
            "rtsp_url": url,
        }
        salvar_config(self.config)
        return True, f"Camera '{nome}' adicionada"

    def scan_rede(self):
        """Procura cameras na rede."""
        if self.callback_voz:
            self.callback_voz("Procurando cameras na rede, Sir. Aguarde 30 segundos.")

        def progresso(n):
            print(f"[CAM SCAN] {n}/254 IPs testados")

        encontradas = scan_rede_cameras(callback_progresso=progresso)
        return encontradas

    def get_url(self, nome):
        cam = self.config["cameras"].get(nome.lower())
        return cam.get("rtsp_url") if cam else None

    def mostrar(self, nome):
        """Manda popup abrir stream da camera."""
        url = self.get_url(nome)
        if not url:
            return False, f"Camera '{nome}' nao configurada"
        if self.callback_popup:
            self.callback_popup({
                "tipo": "camera",
                "nome": nome,
                "url": url,
            })
        return True, f"Mostrando {nome}"

    def mostrar_todas(self):
        cams = self.listar()
        if not cams:
            return False, "Nenhuma camera configurada"
        if self.callback_popup:
            self.callback_popup({
                "tipo": "cameras_grid",
                "cameras": [
                    {"nome": n, "url": c["rtsp_url"]}
                    for n, c in cams.items()
                ],
            })
        return True, f"Mostrando {len(cams)} cameras"


_instance = None


def get_cameras(callback_voz=None, callback_popup=None):
    global _instance
    if _instance is None:
        _instance = CamerasManager(
            callback_voz=callback_voz,
            callback_popup=callback_popup,
        )
    return _instance
