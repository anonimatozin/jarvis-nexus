"""Servidor ESP32 v5 - display interativo + animacoes + gamepad."""
import asyncio
import json
import socket
import threading
import time
import re
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import websockets
    WS_OK = True
except ImportError:
    WS_OK = False

try:
    import pyautogui
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False

try:
    import keyboard
    KEYBOARD_OK = True
except ImportError:
    KEYBOARD_OK = False

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

WS_PORT = 8766


def get_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: return "127.0.0.1"


class ESP32Server:
    def __init__(self, callback_voz=None, callback_comando=None, **kwargs):
        self.callback_voz = callback_voz
        self.callback_comando = callback_comando

        self.clients = set()
        self.thread = None
        self.loop = None
        self.running = False
        self.ip_local = get_ip_local()
        self.estado_atual = "idle"
        self.modo_atual = "--"

        # Anti-spam de mensagem de conexao
        self._ultimo_avisou_conexao = 0
        self._conexao_atual = None  # rastreia client unico

        # Display: ultimo texto mostrado e quando vai voltar pra hora
        self._display_timer_task = None

    def iniciar(self):
        # Inicia fila BLE em background
        self._fila_thread = threading.Thread(
            target=self._fila_loop, daemon=True, name="ESP32Fila"
        )
        self._fila_thread.start()
        if not WS_OK:
            print("[ESP32] websockets nao instalado")
            return False
        if self.running:
            return True
        self.running = True
        self.thread = threading.Thread(target=self._loop_thread, daemon=True, name="esp32_server")
        self.thread.start()
        print(f"[ESP32] Servidor em ws://{self.ip_local}:{WS_PORT}")
        return True

    def parar(self):
        self.running = False
        if self.loop:
            try:
                asyncio.run_coroutine_threadsafe(self._close_all(), self.loop)
            except: pass

    async def _close_all(self):
        for c in list(self.clients):
            try: await c.close()
            except: pass
        self.clients.clear()

    def _loop_thread(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._serve())
        except Exception as e:
            print(f"[ESP32] erro server: {e}")

    async def _serve(self):
        try:
            async with websockets.serve(
                self._handler, "0.0.0.0", WS_PORT,
                ping_interval=20, ping_timeout=10,
            ):
                while self.running:
                    await asyncio.sleep(1)
                    # so manda hora se ta em idle (nao polui display)
                    if self.estado_atual == "idle":
                        await self._broadcast_hora()
        except Exception as e:
            print(f"[ESP32] erro serve: {e}")

    async def _handler(self, websocket):
        addr = websocket.remote_address
        ip_remoto = addr[0] if addr else "?"

        # Se ja tem um client deste IP, fecha o antigo silenciosamente
        for c in list(self.clients):
            try:
                if c.remote_address and c.remote_address[0] == ip_remoto:
                    await c.close()
                    self.clients.discard(c)
            except: pass

        self.clients.add(websocket)
        agora = time.time()
        # So fala "conectado" se passou mais de 60s desde o ultimo aviso
        if agora - self._ultimo_avisou_conexao > 60:
            self._ultimo_avisou_conexao = agora
            print(f"[ESP32] Conectado: {addr}")
            if self.callback_voz:
                try: self.callback_voz("Jarvis Deck conectado, Sir.")
                except: pass
        else:
            print(f"[ESP32] Reconectado silencioso: {addr}")

        await self._enviar(websocket, {
            "tipo": "estado", "estado": self.estado_atual,
        })

        try:
            async for msg in websocket:
                try:
                    data = json.loads(msg)
                    await self._processar(data, websocket)
                except json.JSONDecodeError:
                    pass
        except websockets.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            # Nao fala mais "desconectado" - polui muito

    async def _processar(self, data, websocket):
        tipo = data.get("tipo")

        if tipo == "ping":
            await self._enviar(websocket, {"tipo": "pong"})
            return

        if tipo == "boot":
            print(f"[ESP32] Boot info: {data}")
            return

        if tipo == "keypad":
            tecla = data.get("tecla", "")
            menu = data.get("menu", "")
            cmd = self._tecla_to_comando(tecla, menu)
            if cmd and self.callback_comando:
                try: self.callback_comando(cmd)
                except Exception as e: print(f"[ESP32] erro cmd: {e}")

        # ═══ GAMEPAD (bluepad32) ═══
        if tipo == "botao":
            nome = data.get("nome", "")
            bid = data.get("id", 0)
            print(f"[DECK] Botao {bid} ({nome})")
            await self._processar_botao_gamepad(nome)

        if tipo == "analogico_l":
            pass  # analogico esquerdo (futuro: mover mouse)

        if tipo == "bt_status":
            status = data.get("status", "")
            print(f"[DECK] Controle BT: {status}")

    def _tecla_to_comando(self, tecla, menu=""):
        # Menu MOD
        if menu == "0":
            return {
                "1": "modo trabalho",
                "2": "vou jogar minecraft",
                "3": "preciso focar",
                "4": "vou dormir",
                "5": "vou gravar",
                "6": "quero relaxar",
            }.get(tecla)

        # Menu APP
        if menu == "#":
            return {
                "1": "abrir spotify",
                "2": "abrir discord",
                "3": "abrir chrome",
                "4": "abrir code",
                "5": "abrir minecraft",
                "6": "abrir calculadora",
                "7": "proxima musica",
                "8": "pausar musica",
                "9": "musica anterior",
            }.get(tecla)

        # Diretas
        return {
            "1": "pomodoro",
            "2": "volume 80",
            "3": "volume 30",
            "A": "para de falar",
            "4": "brilho 80",
            "5": "brilho 40",
            "6": "tira uma foto",
            "B": "pausa captura",
            "7": "que horas sao",
            "8": "status do pc",
            "9": "pausa captura",
            "C": "tema laranja",
            "D": "ajuda",
        }.get(tecla)

    # ═══ GAMEPAD — Mapeamento de botoes ═══

    async def _processar_botao_gamepad(self, nome):
        """Processa botao do gamepad (bluepad32)."""
        ACOES_PC = {
            "X":      self._acao_play_pause,
            "LB":     self._acao_musica_anterior,
            "RB":     self._acao_proxima_musica,
            "L2":     self._acao_volume_menos,
            "R2":     self._acao_volume_mais,
            "LSTICK": self._acao_mute,
            "UP":     self._acao_volume_mais,
            "DOWN":   self._acao_volume_menos,
            "LEFT":   self._acao_brilho_menos,
            "RIGHT":  self._acao_brilho_mais,
            "SYSTEM": self._acao_desktop,
            "BACK":   self._acao_alt_tab,
        }

        ACOES_JARVIS = {
            "A":      self._acao_wake,
            "B":      self._acao_cancelar,
            "Y":      self._acao_status_pc,
            "RSTICK": self._acao_screenshot,
        }

        if nome in ACOES_PC:
            try:
                ACOES_PC[nome]()
            except Exception as e:
                print(f"[DECK] erro acao PC {nome}: {e}")

        elif nome in ACOES_JARVIS:
            try:
                await ACOES_JARVIS[nome]()
            except Exception as e:
                print(f"[DECK] erro acao Jarvis {nome}: {e}")

        else:
            print(f"[DECK] botao {nome} sem mapeamento")

    # ───── Acoes PC ─────

    def _acao_play_pause(self):
        if KEYBOARD_OK:
            keyboard.send("play/pause media")
            print("[DECK] Play/Pause")

    def _acao_proxima_musica(self):
        if KEYBOARD_OK:
            keyboard.send("next track")
            print("[DECK] Proxima musica")

    def _acao_musica_anterior(self):
        if KEYBOARD_OK:
            keyboard.send("previous track")
            print("[DECK] Musica anterior")

    def _acao_volume_mais(self):
        if KEYBOARD_OK:
            keyboard.send("volume up")
            keyboard.send("volume up")
            print("[DECK] Volume +")

    def _acao_volume_menos(self):
        if KEYBOARD_OK:
            keyboard.send("volume down")
            keyboard.send("volume down")
            print("[DECK] Volume -")

    def _acao_mute(self):
        if KEYBOARD_OK:
            keyboard.send("volume mute")
            print("[DECK] Mute")

    def _acao_brilho_mais(self):
        try:
            ps = "$b = (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness; " \
                 "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [Math]::Min(100, $b + 10))"
            subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=10)
            print("[DECK] Brilho +")
        except Exception as e:
            print(f"[DECK] Brilho falhou: {e}")

    def _acao_brilho_menos(self):
        try:
            ps = "$b = (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness; " \
                 "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [Math]::Max(0, $b - 10))"
            subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=10)
            print("[DECK] Brilho -")
        except Exception as e:
            print(f"[DECK] Brilho falhou: {e}")

    def _acao_desktop(self):
        if PYAUTOGUI_OK:
            pyautogui.hotkey("win", "d")
            print("[DECK] Desktop (Win+D)")

    def _acao_alt_tab(self):
        if PYAUTOGUI_OK:
            pyautogui.hotkey("alt", "tab")
            print("[DECK] Alt+Tab")

    # ───── Acoes Jarvis ─────

    async def _acao_wake(self):
        """Ativa wake word via deck."""
        print("[DECK] Wake ativado")
        self.set_estado("listening")
        self.mostrar_texto("OUV", 3)
        if self.callback_comando:
            try:
                self.callback_comando("__wake__")
            except Exception:
                pass

    async def _acao_cancelar(self):
        print("[DECK] Cancelar")
        self.set_estado("idle")
        self.mostrar_texto("STOP", 2)
        if self.callback_comando:
            try:
                self.callback_comando("__cancelar__")
            except Exception:
                pass

    async def _acao_status_pc(self):
        if not PSUTIL_OK:
            return
        cpu = int(psutil.cpu_percent(interval=0.5))
        ram = int(psutil.virtual_memory().percent)
        print(f"[DECK] Status: CPU={cpu}% RAM={ram}%")
        self.set_estado("thinking")
        await asyncio.sleep(0.5)
        self.mostrar_numero(cpu, "%")
        await asyncio.sleep(3)
        self.mostrar_numero(ram, "%")
        if self.callback_comando:
            try:
                self.callback_comando(f"__falar__:CPU em {cpu} por cento, memoria em {ram} por cento")
            except Exception:
                pass

    async def _acao_screenshot(self):
        print("[DECK] Screenshot")
        self.set_estado("thinking")
        self.mostrar_texto("CAP", 2)
        if self.callback_comando:
            try:
                self.callback_comando("__screenshot__")
            except Exception:
                pass
        await asyncio.sleep(1)
        self.set_estado("success")
        self.mostrar_texto(" OK", 2)
        await asyncio.sleep(2)
        self.set_estado("idle")

    async def _enviar(self, websocket, data):
        try: await websocket.send(json.dumps(data))
        except: pass

    async def _broadcast(self, data):
        if not self.clients: return
        msg = json.dumps(data)
        for c in list(self.clients):
            try: await c.send(msg)
            except: self.clients.discard(c)

    async def _broadcast_hora(self):
        now = datetime.now()
        await self._broadcast({"tipo": "hora", "h": now.hour, "m": now.minute, "s": now.second})



    def _fila_loop(self):
        """Le data/esp32_queue.json e envia pro ESP32."""
        import json as _j
        fila = Path("data/esp32_queue.json")
        while self.running:
            try:
                if fila.exists() and fila.stat().st_size > 0:
                    with open(str(fila), "r", encoding="utf-8") as f:
                        linhas = f.readlines()
                    fila.write_text("", encoding="utf-8")
                    for linha in linhas:
                        linha = linha.strip()
                        if not linha:
                            continue
                        try:
                            obj = _j.loads(linha)
                            self.enviar_lamp(obj.pop("tipo"), **obj)
                            time.sleep(0.08)
                        except Exception as ex:
                            print(f"[ESP32-FILA] err: {ex}")
            except Exception as ex:
                print(f"[ESP32-FILA] loop err: {ex}")
            time.sleep(0.15)

    def enviar_lamp(self, tipo, **kwargs):
        """Envia comando de lampada BLE pro ESP32. Thread-safe."""
        payload = {"tipo": tipo, **kwargs}
        if self.loop and self.running and self.clients:
            asyncio.run_coroutine_threadsafe(
                self._broadcast(payload),
                self.loop
            )
            return True
        return False

    def lamp_on(self):
        return self.enviar_lamp("lamp_on")

    def lamp_off(self):
        return self.enviar_lamp("lamp_off")

    def lamp_cor(self, cor):
        return self.enviar_lamp("lamp_cor", cor=cor)

    def lamp_brilho(self, valor):
        """valor 0-1000"""
        return self.enviar_lamp("lamp_brilho", valor=valor)

    def set_estado(self, estado):
        """Muda estado (idle/listening/thinking/speaking).
        Quando entra em thinking, manda animacao no display.
        Quando volta pra idle, volta a mostrar hora.
        """
        if estado == self.estado_atual:
            return
        self.estado_atual = estado
        if not self.loop:
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"tipo": "estado", "estado": estado}),
                self.loop
            )
            # Anima display por estado
            if estado == "thinking":
                asyncio.run_coroutine_threadsafe(
                    self._broadcast({"tipo": "display", "texto": "----"}),
                    self.loop
                )
            elif estado == "listening":
                asyncio.run_coroutine_threadsafe(
                    self._broadcast({"tipo": "display", "texto": "HEAR"}),
                    self.loop
                )
            elif estado == "speaking":
                asyncio.run_coroutine_threadsafe(
                    self._broadcast({"tipo": "display", "texto": "TALK"}),
                    self.loop
                )
        except: pass

    def mostrar_texto(self, texto, duracao_seg=8):
        """Mostra texto custom no display por X segundos, depois volta hora."""
        if not self.loop:
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"tipo": "display", "texto": str(texto)[:8]}),
                self.loop
            )
        except: pass

    def mostrar_numero(self, num, sufixo=""):
        """Mostra um numero no display. Ex: 42, '42C', '85%'."""
        if not self.loop:
            return
        try:
            n = int(num) if isinstance(num, (int, float)) else num
            texto = f"{n}{sufixo}" if sufixo else str(n)
            texto = texto[:4].rjust(4)
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"tipo": "display", "texto": texto}),
                self.loop
            )
        except: pass

    def mostrar_resposta(self, resposta_jarvis):
        """Detecta numero importante na resposta do Jarvis e mostra no display.
        Ex: 'CPU 65%' -> mostra '65%'
            '17 graus' -> mostra '17C'
            'sao 14 e 30' -> mostra hora '1430'
        """
        if not resposta_jarvis or not self.loop:
            return
        try:
            txt = str(resposta_jarvis).lower()

            # 1. Temperatura: "17 graus" ou "17°C"
            m = re.search(r"(\d{1,2})\s*(?:graus|°c|°)", txt)
            if m:
                self.mostrar_numero(m.group(1), "C")
                return

            # 2. Porcentagem: "65%" ou "65 por cento"
            m = re.search(r"(\d{1,3})\s*(?:%|por cento)", txt)
            if m:
                self.mostrar_numero(m.group(1), "%")
                return

            # 3. Hora: "sao 14:30" ou "14 e 30"
            m = re.search(r"(\d{1,2})[:\se](\d{2})", txt)
            if m and ("hora" in txt or "sao" in txt[:30]):
                h, mi = int(m.group(1)), int(m.group(2))
                if 0 <= h <= 23 and 0 <= mi <= 59:
                    asyncio.run_coroutine_threadsafe(
                        self._broadcast({"tipo": "hora", "h": h, "m": mi, "s": 0}),
                        self.loop
                    )
                    return

            # 4. Numero solto importante
            m = re.search(r"\b(\d{1,4})\b", txt)
            if m:
                self.mostrar_numero(m.group(1))
                return
        except Exception as e:
            print(f"[ESP32] mostrar_resposta erro: {e}")

    def extrair_numero_display(self, texto):
        """Extrai numero relevante de texto e mostra no display do deck.
        Chamado pelo engine antes de falar."""
        if not texto:
            return
        txt = str(texto).lower()
        # Temperatura
        m = re.search(r"(\d{1,2})\s*(?:graus|°c|°)", txt)
        if m:
            self.mostrar_numero(m.group(1), "C")
            return
        # Porcentagem
        m = re.search(r"(\d{1,3})\s*(?:%|por cento)", txt)
        if m:
            self.mostrar_numero(m.group(1), "%")
            return
        # Numero solto
        m = re.search(r"\b(\d{1,4})\b", txt)
        if m:
            self.mostrar_numero(m.group(1))

    def enviar_temperatura(self, celsius):
        """Envia temperatura pro display do deck."""
        if not self.loop:
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"tipo": "temperatura", "c": int(celsius)}),
                self.loop
            )
        except: pass

    def piscar_alerta(self):
        if self.loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self._broadcast({"tipo": "alerta"}),
                    self.loop
                )
            except: pass

    def mostrar_stats_legiao(self, vivos, total, mortes=0):
        """Mostra placar tipo futebol: '12/18' ou rotativo vivos/mortes."""
        if not self.loop:
            return
        try:
            texto = f"{vivos:02d}/{total:02d}"[:4]
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"tipo": "display", "texto": texto}),
                self.loop
            )
        except: pass

    def status(self):
        return {
            "rodando": self.running,
            "ip": self.ip_local,
            "porta": WS_PORT,
            "clients": len(self.clients),
            "estado": self.estado_atual,
        }


_instance = None


def get_esp32_server(callback_voz=None, callback_comando=None, **kwargs):
    """kwargs aceita callbacks antigos pra compatibilidade (ignora)."""
    global _instance
    if _instance is None:
        _instance = ESP32Server(
            callback_voz=callback_voz,
            callback_comando=callback_comando,
        )
    return _instance
