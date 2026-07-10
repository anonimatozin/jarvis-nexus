"""
Legion Manager v3 - so reage a eventos REAIS do master.
"""
import asyncio
import json
import os
import subprocess
import threading
import time
import socket
from pathlib import Path

try:
    import websockets
    WS_OK = True
except ImportError:
    WS_OK = False

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

LEGION_DIR = Path("bot_minecraft/legion")
MASTER_WS_URL = "ws://localhost:8768"
MASTER_WS_PORT = 8768


def porta_em_uso(porta):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try: return s.connect_ex(("127.0.0.1", porta)) == 0
    except: return False
    finally: s.close()


def matar_legiao():
    if not PSUTIL_OK: return 0
    mortos = 0
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["name"] and "node" in proc.info["name"].lower():
                    cmd = " ".join(proc.info.get("cmdline") or [])
                    if "legion_master_v2" in cmd or "soldier.js" in cmd:
                        proc.kill()
                        mortos += 1
            except: pass
    except: pass
    return mortos


class LegionManager:
    def __init__(self, callback_voz=None, callback_display=None):
        self.callback_voz = callback_voz
        self.callback_display = callback_display
        self.master_process = None
        self.ws = None
        self.loop = None
        self.thread = None
        self.conectado = False

        # Estado
        self.online_qtd = 0
        self.numeros_online = []
        self.ultimo_id = 0
        self.proximo_id = 1
        self.total_mortos = 0
        self.modo = "standby"

        # Anti-spam de notificacao
        self._ult_notif_morte = 0

    def iniciar_master(self):
        if porta_em_uso(MASTER_WS_PORT):
            print("[LEGION] Master ja rodando")
            self._iniciar_thread_ws()
            return True, "Master ja ativo"

        master_js = LEGION_DIR / "legion_master_v2.js"
        if not master_js.exists():
            return False, "legion_master_v2.js nao existe"

        try:
            flags = 0
            if os.name == "nt":
                flags = subprocess.CREATE_NO_WINDOW
            self.master_process = subprocess.Popen(
                ["node", "legion_master_v2.js"],
                cwd=str(LEGION_DIR),
                creationflags=flags,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
            )
            print(f"[LEGION] Master iniciado PID={self.master_process.pid}")
            time.sleep(2)
            self._iniciar_thread_ws()
            return True, "Master online"
        except Exception as e:
            return False, f"Erro: {e}"

    def parar_tudo(self):
        try:
            matar_legiao()
            self.conectado = False
            self.ws = None
            self.master_process = None
            return True
        except: return False

    def _iniciar_thread_ws(self):
        if self.thread and self.thread.is_alive(): return
        self.thread = threading.Thread(target=self._ws_loop, daemon=True, name="legion_ws")
        self.thread.start()

    def _ws_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try: self.loop.run_until_complete(self._conectar())
        except Exception as e: print(f"[LEGION WS] {e}")

    async def _conectar(self):
        if not WS_OK: return
        ws = None
        for _ in range(20):
            try:
                ws = await asyncio.wait_for(websockets.connect(MASTER_WS_URL), timeout=2)
                break
            except: await asyncio.sleep(1)
        if not ws: return
        self.ws = ws
        self.conectado = True
        print("[LEGION] Conectado ao master")
        try:
            async for msg in ws:
                try: self._processar(json.loads(msg))
                except: pass
        except: pass
        finally:
            self.conectado = False
            self.ws = None

    def _processar(self, data):
        tipo = data.get("tipo")

        if tipo == "status":
            self.online_qtd = data.get("online_qtd", 0)
            self.numeros_online = data.get("numeros_online", [])
            self.ultimo_id = data.get("ultimo_id", 0)
            self.proximo_id = data.get("proximo_id", 1)
            self.total_mortos = data.get("total_mortos", 0)
            self.modo = data.get("modo", "standby")
            if self.callback_display and self.online_qtd > 0:
                try:
                    txt = f"{self.online_qtd:02d}"
                    self.callback_display(txt)
                except: pass

        elif tipo == "log":
            # Log real do master, mostra no console Python
            print(f"  [LEGION] {data.get('msg', '')}")

        elif tipo == "soldado_online":
            num = data.get("numero")
            prog = data.get("progresso", "")
            print(f"  [LEGION] legiao_de_ferro{num} ONLINE ({prog})")

        elif tipo == "soldado_falhou":
            num = data.get("numero")
            print(f"  [LEGION] legiao_de_ferro{num} FALHOU")

        elif tipo == "criacao_finalizada":
            criados = data.get("criados", [])
            falhas = data.get("falhas", [])
            if self.callback_voz:
                if criados:
                    msg = f"Legiao pronta. {len(criados)} unidades ativas: do {criados[0]} ao {criados[-1]}."
                    if falhas:
                        msg += f" {len(falhas)} falharam."
                    self.callback_voz(msg)
                else:
                    self.callback_voz(f"Falha total. Nenhum soldado entrou.")

        elif tipo == "soldado_morreu_real":
            num = data.get("numero")
            motivo = data.get("motivo", "?")
            print(f"  [LEGION] MORTE REAL: legiao_de_ferro{num} ({motivo})")
            # Anti-spam (max 1 fala a cada 3s)
            agora = time.time()
            if self.callback_voz and (agora - self._ult_notif_morte) > 3:
                self._ult_notif_morte = agora
                self.callback_voz(f"Soldado {num} caiu, Sir.")

        elif tipo == "substituto_online":
            num = data.get("numero")
            print(f"  [LEGION] Substituto ONLINE: legiao_de_ferro{num}")
            if self.callback_voz:
                self.callback_voz(f"Substituto {num} em campo.")

    async def _enviar(self, data):
        if self.ws:
            try: await self.ws.send(json.dumps(data))
            except: pass

    def _send_sync(self, data):
        if not self.loop or not self.conectado: return False
        try:
            asyncio.run_coroutine_threadsafe(self._enviar(data), self.loop)
            return True
        except: return False

    # ═══════ COMANDOS PUBLICOS ═══════

    def criar_legiao(self, qtd):
        if not self.conectado:
            ok, msg = self.iniciar_master()
            if not ok: return False
            time.sleep(3)
        return self._send_sync({"tipo": "criar", "qtd": int(qtd)})

    def seguir(self, alvo=None):
        return self._send_sync({
            "tipo": "modo", "modo": "seguir",
            "dados": {"alvo": alvo} if alvo else {},
        })

    def proteger(self, alvo):
        return self._send_sync({
            "tipo": "modo", "modo": "proteger",
            "dados": {"alvo": alvo},
        })

    def parar(self):
        return self._send_sync({"tipo": "modo", "modo": "standby"})

    def defender_pos(self, pos):
        return self._send_sync({
            "tipo": "modo", "modo": "defender_pos",
            "dados": {"pos": pos},
        })

    def atacar(self, alvo):
        return self._send_sync({
            "tipo": "modo", "modo": "atacar",
            "dados": {"alvo": alvo},
        })

    def dispersar(self):
        return self._send_sync({"tipo": "dispersar"})

    def resetar_db(self):
        return self._send_sync({"tipo": "reset_db"})

    def status(self):
        return {
            "conectado": self.conectado,
            "online_qtd": self.online_qtd,
            "numeros_online": self.numeros_online,
            "ultimo_id": self.ultimo_id,
            "proximo_id": self.proximo_id,
            "total_mortos": self.total_mortos,
            "modo": self.modo,
        }

    def status_texto(self):
        s = self.status()
        if not s["conectado"]:
            return "Legiao offline, Sir."
        if s["online_qtd"] == 0:
            return f"Nenhum soldado ativo. Total criados: {s['ultimo_id']}, mortos: {s['total_mortos']}."
        nums = s["numeros_online"][:10]
        nums_str = ", ".join(str(n) for n in nums)
        msg = f"{s['online_qtd']} soldados ativos ({nums_str}"
        if len(s["numeros_online"]) > 10: msg += "..."
        msg += f"). Total criados: {s['ultimo_id']}, mortos: {s['total_mortos']}."
        return msg


_instance = None

def get_legion(callback_voz=None, callback_display=None):
    global _instance
    if _instance is None:
        _instance = LegionManager(callback_voz=callback_voz, callback_display=callback_display)
    return _instance
