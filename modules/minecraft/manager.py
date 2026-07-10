"""
Manager v2 - mata zumbi + abre bot em janela visivel.
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

BOT_DIR = Path("bot_minecraft")
WS_URL = "ws://localhost:8765"
WS_PORT = 8765


def porta_em_uso(porta):
    """Checa se porta esta ocupada."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        result = s.connect_ex(("127.0.0.1", porta))
        return result == 0
    except Exception:
        return False
    finally:
        s.close()


def matar_bots_zumbi():
    """Mata qualquer node.js rodando o bot."""
    if not PSUTIL_OK:
        return 0
    mortos = 0
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["name"] and "node" in proc.info["name"].lower():
                    cmd = proc.info.get("cmdline") or []
                    cmd_str = " ".join(cmd)
                    if "bot_minecraft" in cmd_str or "index.js" in cmd_str:
                        print(f"[MC] Matando bot zumbi PID {proc.info['pid']}")
                        proc.kill()
                        mortos += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        print(f"[MC] erro matar zumbi: {e}")
    return mortos


class MinecraftManager:
    def __init__(self, callback_voz=None):
        self.callback_voz = callback_voz
        self.bot_process = None
        self.ws = None
        self.conectado = False
        self.status_atual = {}
        self.loop = None
        self.thread = None
        self._ws_task = None

    def is_node_ok(self):
        node_modules = BOT_DIR / "node_modules"
        return node_modules.exists() and (node_modules / "mineflayer").exists()

    def bot_rodando(self):
        """Verifica se ja tem bot rodando pela porta WS."""
        return porta_em_uso(WS_PORT)

    def iniciar_bot(self):
        """Inicia bot. Mata zumbis primeiro."""
        if not self.is_node_ok():
            return False, "Bot Node nao instalado. Rode script19a."

        # Se ja tem bot rodando, retorna
        if self.bot_rodando():
            if self.conectado:
                return False, "Bot ja esta rodando e conectado."
            # Porta ocupada mas nao conectado = zumbi
            print("[MC] Porta 8765 ocupada por zumbi, matando...")
            matar_bots_zumbi()
            time.sleep(2)

        if not (BOT_DIR / "index.js").exists():
            return False, f"Arquivo index.js nao existe"

        try:
            # Roda SEM janela CMD (oculto em background)
            flags = 0
            if os.name == "nt":
                flags = subprocess.CREATE_NO_WINDOW

            self.bot_process = subprocess.Popen(
                ["node", "index.js"],
                cwd=str(BOT_DIR),
                creationflags=flags,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
            )

            print(f"[MC] Bot iniciado (sem janela) PID={self.bot_process.pid}")

            # Inicia thread WS
            if self.thread and self.thread.is_alive():
                # Para o anterior
                self.conectado = False
            self.thread = threading.Thread(target=self._ws_loop, daemon=True)
            self.thread.start()

            return True, "Bot iniciado em background, Sir."
        except Exception as e:
            return False, f"Erro: {e}"

    def parar_bot(self):
        """Para o bot e mata zumbis."""
        try:
            mortos = matar_bots_zumbi()
            self.conectado = False
            self.ws = None
            if self.bot_process:
                try:
                    self.bot_process.terminate()
                except: pass
                self.bot_process = None
            return mortos > 0 or True
        except Exception as e:
            print(f"[MC] erro parar: {e}")
            return False

    def status(self):
        if not self.bot_rodando():
            return {"online": False, "msg": "Bot offline"}
        if not self.conectado:
            return {"online": True, "conectado": False, "msg": "Conectando..."}
        return self.status_atual

    def enviar_comando(self, cmd):
        if not self.ws or not self.conectado or not self.loop:
            return False
        try:
            asyncio.run_coroutine_threadsafe(
                self._send({"tipo": "comando", "cmd": cmd}),
                self.loop
            )
            return True
        except Exception as e:
            print(f"[MC] erro enviar: {e}")
            return False

    async def _send(self, data):
        if self.ws:
            try:
                await self.ws.send(json.dumps(data))
            except Exception as e:
                print(f"[MC] send erro: {e}")

    def _ws_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._conectar_e_escutar())
        except Exception as e:
            print(f"[MC] loop erro: {e}")

    async def _conectar_e_escutar(self):
        if not WS_OK:
            print("[MC] websockets nao instalado")
            return

        # Aguarda WS subir (max 30s)
        ws = None
        for i in range(30):
            try:
                ws = await asyncio.wait_for(
                    websockets.connect(WS_URL),
                    timeout=2
                )
                break
            except Exception:
                await asyncio.sleep(1)

        if not ws:
            print("[MC] Falha ao conectar WebSocket (30s timeout)")
            if self.callback_voz:
                self.callback_voz(
                    "Sir, nao consegui conectar no bot. "
                    "Verifica a janela 'Jarvis MC Bot' pra ver o erro."
                )
            return

        self.ws = ws
        self.conectado = True
        print("[MC] Conectado ao bot via WebSocket")

        try:
            async for msg in ws:
                try:
                    data = json.loads(msg)
                    self._processar_evento(data)
                except Exception as e:
                    print(f"[MC] erro msg: {e}")
        except websockets.ConnectionClosed:
            print("[MC] WS fechou normalmente")
        except Exception as e:
            print(f"[MC] WS erro: {e}")
        finally:
            self.conectado = False
            self.ws = None

    def _processar_evento(self, data):
        tipo = data.get("tipo")

        if tipo == "spawned":
            if self.callback_voz:
                self.callback_voz("Bot conectou no Minecraft, Sir.")

        elif tipo == "aviso":
            msg = data.get("msg", "")
            if self.callback_voz and msg:
                self.callback_voz(msg)

        elif tipo == "morte":
            pos = data.get("pos")
            if pos and self.callback_voz:
                self.callback_voz(
                    f"Sir, morri em X:{int(pos.get('x',0))}, "
                    f"Y:{int(pos.get('y',0))}, Z:{int(pos.get('z',0))}."
                )

        elif tipo == "chat":
            user = data.get("user", "?")
            msg = data.get("msg", "")
            print(f"[MC CHAT] {user}: {msg}")

        elif tipo == "status":
            self.status_atual = data

        elif tipo == "kicked":
            if self.callback_voz:
                self.callback_voz(
                    f"Sir, fui kickado: {data.get('reason', '?')[:80]}"
                )

        elif tipo == "erro":
            print(f"[MC ERRO] {data.get('msg', '?')}")

        elif tipo == "desconectou":
            print(f"[MC] Bot desconectou: {data.get('reason', '?')}")


_instance = None


def get_minecraft(callback_voz=None):
    global _instance
    if _instance is None:
        _instance = MinecraftManager(callback_voz=callback_voz)
    return _instance
