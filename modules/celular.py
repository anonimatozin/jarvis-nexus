# modules/celular.py
"""
J.A.R.V.I.S. - Controle Celular Android v1.0
Via ADB (Android Debug Bridge) - controle total do celular.
"""

import os
import re
import json
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.logger import setup_logger, print_success, print_error, print_system

logger = setup_logger("celular")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

CONFIG_FILE = DATA_DIR / "celular_config.json"


class CelularADB:
    """Controla celular Android via ADB."""

    def __init__(self):
        self.adb_path = self._find_adb()
        self.device_id = None
        self.connected = False
        self._config = self._carregar_config()
        self._notificacoes_cache = []
        self._ultimo_check = None

        if self.adb_path:
            self._detectar_device()

    def _find_adb(self) -> Optional[str]:
        """Encontra o executável do ADB."""
        # Verifica PATH
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            if result.returncode == 0:
                return "adb"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Caminhos comuns no Windows
        common_paths = [
            r"C:\platform-tools\adb.exe",
            r"C:\Android\platform-tools\adb.exe",
            r"C:\Users\Administrator\AppData\Local\Android\Sdk\platform-tools\adb.exe",
            r"C:\Program Files (x86)\Android\platform-tools\adb.exe",
            os.path.expanduser(r"~\AppData\Local\Android\Sdk\platform-tools\adb.exe"),
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    def _carregar_config(self) -> Dict:
        try:
            if CONFIG_FILE.exists():
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {"devices": {}, "aliases": {}}

    def _salvar_config(self):
        try:
            CONFIG_FILE.write_text(
                json.dumps(self._config, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Erro salvar config: {e}")

    def _run_adb(self, args: List[str], timeout: int = 15) -> Tuple[bool, str]:
        """Executa comando ADB e retorna (sucesso, output)."""
        if not self.adb_path:
            return False, "ADB não encontrado. Instale: https://developer.android.com/tools/adb"

        cmd = [self.adb_path]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            output = result.stdout.strip()
            error = result.stderr.strip()

            if result.returncode == 0:
                return True, output
            else:
                return False, error or output
        except subprocess.TimeoutExpired:
            return False, "Comando excedeu tempo limite"
        except FileNotFoundError:
            return False, "ADB não encontrado"
        except Exception as e:
            return False, str(e)

    def _detectar_device(self):
        """Detecta dispositivos conectados."""
        ok, output = self._run_adb(["devices"])
        if not ok:
            self.connected = False
            return

        lines = output.strip().split("\n")
        for line in lines[1:]:
            if "\tdevice" in line:
                self.device_id = line.split("\t")[0]
                self.connected = True
                print_success(f"[CELULAR] Dispositivo: {self.device_id}")
                return

        self.connected = False
        print_error("[CELULAR] Nenhum dispositivo conectado")

    def verificar_conexao(self) -> str:
        """Verifica status da conexão."""
        if not self.adb_path:
            return "ADB não instalado. Baixe em: https://developer.android.com/tools/adb"

        self._detectar_device()

        if self.connected:
            # Pega informações do dispositivo
            ok, modelo = self._run_adb(["shell", "getprop", "ro.product.model"])
            ok2, versao = self._run_adb(["shell", "getprop", "ro.build.version.release"])
            return f"Conectado: {modelo} (Android {versao}) - ID: {self.device_id}"

        return "Nenhum dispositivo conectado. Verifique se a depuração USB está ativa."

    # ═══ NOTIFICAÇÕES ═══

    def ler_notificacoes(self) -> str:
        """Lê notificações recentes do celular."""
        ok, output = self._run_adb(["shell", "dumpsys", "notification", "--noredact"])
        if not ok:
            return "Não consegui ler notificações."

        notificacoes = []
        pkg_atual = ""

        for line in output.split("\n"):
            line = line.strip()

            # Detecta pacote
            if "pkg=" in line:
                m = re.search(r"pkg=(\S+)", line)
                if m:
                    pkg_atual = m.group(1)

            # Detecta título
            if "title=" in line and pkg_atual:
                m = re.search(r"title=(.+?)(?:,|$)", line)
                if m:
                    titulo = m.group(1).strip()
                    if titulo and titulo != "null":
                        notificacoes.append({
                            "app": pkg_atual,
                            "titulo": titulo,
                        })

        if not notificacoes:
            return "Nenhuma notificação recente."

        # Remove duplicatas
        vistas = set()
        unicas = []
        for n in notificacoes:
            chave = f"{n['app']}:{n['titulo']}"
            if chave not in vistas:
                vistas.add(chave)
                unicas.append(n)

        linhas = [f"Notificações ({len(unicas)}):"]
        for n in unicas[:10]:
            app = n["app"].split(".")[-1]  # Nome curto
            linhas.append(f"  • [{app}] {n['titulo']}")

        return "\n".join(linhas)

    # ═══ SMS ═══

    def enviar_sms(self, numero: str, mensagem: str) -> str:
        """Envia SMS via ADB (abre o app de mensagens)."""
        # ADB não pode enviar SMS direto, mas pode abrir o app com a mensagem
        # Usa Intent para abrir o app de SMS com destinatário e mensagem
        cmd = [
            "shell", "am", "start",
            "-a", "android.intent.action.SENDTO",
            "-d", f"sms:{numero}",
            "--es", "sms_body", mensagem,
            "--ez", "exit_on_sent", "true"
        ]
        ok, output = self._run_adb(cmd)
        if ok:
            return f"App de SMS aberto para {numero}. Mensagem pronta para enviar."
        return f"Erro ao abrir SMS: {output}"

    def ler_sms_recentes(self, limite: int = 10) -> str:
        """Lê SMS recentes (requer permissão)."""
        # Tenta ler via content provider
        ok, output = self._run_adb([
            "shell", "content", "query",
            "--uri", "content://sms/inbox",
            "--projection", "address:body:date",
            "--sort", "date DESC"
        ], timeout=10)

        if not ok or not output or "No result" in output:
            return "Não foi possível ler SMS. Verifique as permissões."

        sms_list = []
        for line in output.split("\n"):
            if "Row:" in line:
                m = re.search(r"address=(.+?), body=(.+?), date=(\d+)", line)
                if m:
                    addr = m.group(1).strip()
                    body = m.group(2).strip()
                    sms_list.append(f"  • [{addr}] {body}")

        if not sms_list:
            return "Nenhum SMS recente."

        return f"SMS recentes:\n" + "\n".join(sms_list[:limite])

    # ═══ APPS ═══

    def abrir_app(self, pacote: str) -> str:
        """Abre um app pelo pacote."""
        # Mapeamento de nomes comuns para pacotes
        APPS = {
            "instagram": "com.instagram.android",
            "whatsapp": "com.whatsapp",
            "telegram": "org.telegram.messenger",
            "youtube": "com.google.android.youtube",
            "chrome": "com.android.chrome",
            "spotify": "com.spotify.music",
            "twitter": "com.twitter.android",
            "tiktok": "com.zhiliaoapp.musically",
            "netflix": "com.netflix.mediaclient",
            "maps": "com.google.android.apps.maps",
            "gmail": "com.google.android.gm",
            "drive": "com.google.android.apps.docs",
            "camera": "com.android.camera",
            "galeria": "com.google.android.apps.photos",
            "configuracoes": "com.android.settings",
            "calculator": "com.google.android.calculator",
            "relogio": "com.google.android.deskclock",
            "agenda": "com.google.android.calendar",
            "contatos": "com.google.android.contacts",
            "telefone": "com.android.dialer",
            "sms": "com.google.android.apps.messaging",
        }

        pacote_lower = pacote.lower()
        pacote_real = APPS.get(pacote_lower, pacote)

        # Tenta abrir via monkey (mais confiável)
        ok, output = self._run_adb([
            "shell", "monkey", "-p", pacote_real,
            "-c", "android.intent.category.LAUNCHER", "1"
        ])

        if ok:
            return f"Abrindo {pacote}, Sir."

        # Fallback: tenta via am start
        ok2, output2 = self._run_adb([
            "shell", "am", "start", "-n",
            f"{pacote_real}/.MainActivity"
        ])

        if ok2:
            return f"Abrindo {pacote}, Sir."

        return f"Não consegui abrir {pacote}. Verifique se está instalado."

    def listar_apps(self, terceiros: bool = True) -> str:
        """Lista apps instalados."""
        flag = "-3" if terceiros else ""
        ok, output = self._run_adb(["shell", "pm", "list", "packages", flag])

        if not ok:
            return "Erro ao listar apps."

        pacotes = []
        for line in output.split("\n"):
            if line.startswith("package:"):
                pacote = line.replace("package:", "").strip()
                if pacote:
                    pacotes.append(pacote)

        if not pacotes:
            return "Nenhum app encontrado."

        # Mapeia nomes
        APP_NAMES = {
            "com.instagram.android": "Instagram",
            "com.whatsapp": "WhatsApp",
            "org.telegram.messenger": "Telegram",
            "com.google.android.youtube": "YouTube",
            "com.android.chrome": "Chrome",
            "com.spotify.music": "Spotify",
            "com.twitter.android": "Twitter",
            "com.zhiliaoapp.musically": "TikTok",
            "com.netflix.mediaclient": "Netflix",
            "com.google.android.apps.maps": "Maps",
            "com.google.android.gm": "Gmail",
        }

        linhas = [f"Apps instalados ({len(pacotes)}):"]
        for p in sorted(pacotes)[:30]:
            nome = APP_NAMES.get(p, p.split(".")[-1])
            linhas.append(f"  • {nome}")

        if len(pacotes) > 30:
            linhas.append(f"  ... e mais {len(pacotes) - 30}")

        return "\n".join(linhas)

    def fechar_app(self, pacote: str) -> str:
        """Força fechar um app."""
        ok, output = self._run_adb(["shell", "am", "force-stop", pacote])
        if ok:
            return f"Fechando {pacote}, Sir."
        return f"Erro ao fechar {pacote}."

    # ═══ BATERIA ═══

    def status_bateria(self) -> str:
        """Retorna status da bateria."""
        ok, output = self._run_adb(["shell", "dumpsys", "battery"])
        if not ok:
            return "Não consegui ler bateria."

        info = {}
        for line in output.split("\n"):
            line = line.strip()
            if "level:" in line:
                info["nivel"] = line.split(":")[1].strip()
            elif "status:" in line:
                info["status"] = line.split(":")[1].strip()
            elif "temperature:" in line:
                temp = line.split(":")[1].strip()
                info["temperatura"] = f"{int(temp)/10:.1f}°C" if temp.isdigit() else temp
            elif "voltage:" in line:
                volt = line.split(":")[1].strip()
                info["tensao"] = f"{int(volt)/1000:.2f}V" if volt.isdigit() else volt

        nivel = info.get("nivel", "?")
        status_map = {
            "2": "Carregando",
            "3": "Não carregando",
            "4": "Cheio",
            "5": "Sem bateria",
        }
        status = status_map.get(info.get("status", ""), info.get("status", "?"))
        temp = info.get("temperatura", "?")

        return f"Bateria: {nivel}% ({status}) - Temp: {temp}"

    # ═══ CONTROLES DO CELULAR ═══

    def volume(self, nivel: Optional[int] = None, direcao: Optional[str] = None) -> str:
        """Controla volume do celular."""
        if nivel is not None:
            # Seta volume específico (0-15)
            nivel = max(0, min(15, nivel))
            ok, _ = self._run_adb(["shell", "media", "volume", "--set", str(nivel)])
            if ok:
                return f"Volume: {nivel}/15"
        elif direcao:
            if direcao == "up":
                ok, _ = self._run_adb(["shell", "media", "volume", "--adjust", "raise"])
                return "Volume +"
            elif direcao == "down":
                ok, _ = self._run_adb(["shell", "media", "volume", "--adjust", "lower"])
                return "Volume -"
            elif direcao == "mute":
                ok, _ = self._run_adb(["shell", "media", "volume", "--mute"])
                return "Mudo"
        return "Volume alterado."

    def wifi(self, ligar: Optional[bool] = None) -> str:
        """Controla Wi-Fi."""
        if ligar is None:
            # Consulta status
            ok, output = self._run_adb(["shell", "settings", "get", "global", "wifi_on"])
            status = "Ligado" if output.strip() == "1" else "Desligado"
            return f"Wi-Fi: {status}"

        valor = "1" if ligar else "0"
        ok, _ = self._run_adb(["shell", "svc", "wifi", "enable" if ligar else "disable"])
        return f"Wi-Fi {'ligado' if ligar else 'desligado'}."

    def bluetooth(self, ligar: Optional[bool] = None) -> str:
        """Controla Bluetooth."""
        if ligar is None:
            ok, output = self._run_adb(["shell", "settings", "get", "global", "bluetooth_on"])
            status = "Ligado" if output.strip() == "1" else "Desligado"
            return f"Bluetooth: {status}"

        if ligar:
            ok, _ = self._run_adb(["shell", "svc", "bluetooth", "enable"])
        else:
            ok, _ = self._run_adb(["shell", "svc", "bluetooth", "disable"])
        return f"Bluetooth {'ligado' if ligar else 'desligado'}."

    def tela(self, acao: str) -> str:
        """Controla tela (ligar/desligar/bloquear/desbloquear)."""
        if acao == "ligar" or acao == "on":
            ok, _ = self._run_adb(["shell", "input", "keyevent", "224"])  # KEYCODE_WAKEUP
            return "Tela ligada."
        elif acao == "desligar" or acao == "off":
            ok, _ = self._run_adb(["shell", "input", "keyevent", "223"])  # KEYCODE_SLEEP
            return "Tela desligada."
        elif acao == "desbloquear":
            # Swipe up para desbloquear
            ok, _ = self._run_adb(["shell", "input", "swipe", "540", "1800", "540", "600", "300"])
            time.sleep(0.5)
            return "Tela desbloqueada."
        return "Ação de tela inválida."

    def screenshot(self) -> str:
        """Tira screenshot e retorna caminho."""
        remote_path = "/sdcard/screenshot_jarvis.png"
        local_path = str(DATA_DIR / "celular_screenshot.png")

        ok, _ = self._run_adb(["shell", "screencap", "-p", remote_path])
        if not ok:
            return "Erro ao tirar screenshot."

        ok2, _ = self._run_adb(["pull", remote_path, local_path])
        if ok2:
            self._run_adb(["shell", "rm", remote_path])
            return f"Screenshot salvo: {local_path}"

        return "Erro ao transferir screenshot."

    def localizar(self) -> str:
        """Faz o celular tocar (ring)."""
        # Abre o app de encontrar dispositivo
        ok, _ = self._run_adb([
            "shell", "am", "start",
            "-a", "com.google.android.gms.location.RECEIVED",
            "-n", "com.google.android.gms/.location.settings.LocationHistorySettingsActivity"
        ])
        if ok:
            return "Procurando dispositivo... (verifique o app Encontre Meu Dispositivo)"

        # Fallback: toca alarme
        ok2, _ = self._run_adb(["shell", "media", "volume", "--set", "15"])
        ok3, _ = self._run_adb(["shell", "am", "start", "-a", "android.intent.action.SET_ALARM"])
        return "Alarme tocando no celular."

    def transferir_arquivo(self, caminho_pc: str, destino: str = "/sdcard/") -> str:
        """Transfere arquivo do PC para o celular."""
        if not os.path.exists(caminho_pc):
            return "Arquivo não encontrado no PC."

        ok, output = self._run_adb(["push", caminho_pc, destino])
        if ok:
            nome = os.path.basename(caminho_pc)
            return f"Arquivo '{nome}' transferido para {destino}"
        return f"Erro ao transferir: {output}"

    def receber_arquivo(self, caminho_celular: str) -> str:
        """Transfere arquivo do celular para o PC."""
        local_path = str(DATA_DIR / "recebido_" + os.path.basename(caminho_celular))

        ok, output = self._run_adb(["pull", caminho_celular, local_path])
        if ok:
            return f"Arquivo recebido: {local_path}"
        return f"Erro ao receber: {output}"

    # ═══ INFORMAÇÕES ═══

    def info_celular(self) -> str:
        """Retorna informações gerais do celular."""
        info = {}
        comandos = {
            "modelo": ["shell", "getprop", "ro.product.model"],
            "marca": ["shell", "getprop", "ro.product.brand"],
            "android": ["shell", "getprop", "ro.build.version.release"],
            "sdk": ["shell", "getprop", "ro.build.version.sdk"],
            "ip": ["shell", "ip", "route", "show", "dev", "wlan0"],
            "armazenamento": ["shell", "df", "/sdcard"],
        }

        for key, cmd in comandos.items():
            ok, output = self._run_adb(cmd)
            if ok:
                info[key] = output.strip()

        linhas = ["Informações do celular:"]
        if info.get("modelo"):
            linhas.append(f"  • Modelo: {info['marca']} {info['modelo']}")
        if info.get("android"):
            linhas.append(f"  • Android: {info['android']} (SDK {info.get('sdk', '?')})")
        if info.get("ip"):
            for line in info["ip"].split("\n"):
                if "src" in line:
                    m = re.search(r"src (\S+)", line)
                    if m:
                        linhas.append(f"  • IP: {m.group(1)}")
                        break

        return "\n".join(linhas)

    def status_completo(self) -> str:
        """Status completo do celular."""
        bateria = self.status_bateria()
        info = self.info_celular()
        return f"{info}\n{bateria}"


# ═══ SINGLETON ═══

_celular_instance = None

def get_celular():
    global _celular_instance
    if _celular_instance is None:
        _celular_instance = CelularADB()
    return _celular_instance
