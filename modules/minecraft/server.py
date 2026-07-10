"""
Servidor Minecraft local (Paper 1.21.1).
Controla via Jarvis: 'liga servidor' / 'desliga servidor'.
"""
import os
import subprocess
import threading
import time
import socket
from pathlib import Path

SERVER_DIR = Path("mc_server")
SERVER_PORT = 25565


def porta_em_uso(porta):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        return s.connect_ex(("127.0.0.1", porta)) == 0
    except: return False
    finally:
        s.close()


def matar_servidor():
    """Mata processo java do server."""
    try:
        import psutil
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["name"] and "java" in proc.info["name"].lower():
                    cmd = " ".join(proc.info.get("cmdline") or [])
                    if "paper.jar" in cmd:
                        proc.terminate()
                        time.sleep(2)
                        try: proc.kill()
                        except: pass
                        return True
            except: pass
    except: pass
    return False


class MinecraftServer:
    def __init__(self, callback_voz=None):
        self.callback_voz = callback_voz
        self.processo = None
        self.thread_log = None
        self.rodando = False
        self.iniciado_em = None
        self.players_online = []

    def esta_rodando(self):
        return porta_em_uso(SERVER_PORT)

    def iniciar(self):
        if self.esta_rodando():
            return False, "Servidor ja esta rodando."

        jar = SERVER_DIR / "paper.jar"
        if not jar.exists():
            return False, "paper.jar nao encontrado. Roda instalar_paper_server.py"

        try:
            flags = 0
            if os.name == "nt":
                flags = subprocess.CREATE_NO_WINDOW

            cmd = [
                "java",
                "-Xms2G", "-Xmx4G",
                "-XX:+UseG1GC",
                "-XX:+ParallelRefProcEnabled",
                "-XX:MaxGCPauseMillis=200",
                "-jar", "paper.jar", "nogui"
            ]

            self.processo = subprocess.Popen(
                cmd,
                cwd=str(SERVER_DIR),
                creationflags=flags,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            self.rodando = True
            self.iniciado_em = time.time()
            print(f"[MC SERVER] Iniciado PID={self.processo.pid}")

            # Thread pra monitorar log e detectar "Done"
            self.thread_log = threading.Thread(
                target=self._monitorar_log, daemon=True
            )
            self.thread_log.start()

            return True, "Servidor iniciando, Sir. Aguarde 30 a 60 segundos."
        except Exception as e:
            return False, f"Erro: {e}"

    def _monitorar_log(self):
        """Le stdout do server pra detectar eventos."""
        if not self.processo:
            return
        pronto_avisado = False
        try:
            for linha in self.processo.stdout:
                linha = linha.strip()
                if not linha:
                    continue

                # Server pronto
                if "Done" in linha and not pronto_avisado:
                    pronto_avisado = True
                    print(f"[MC SERVER] PRONTO!")
                    if self.callback_voz:
                        try:
                            self.callback_voz(
                                "Servidor Minecraft pronto, Sir. "
                                "Pode conectar em localhost porta 25565."
                            )
                        except: pass

                # Player entrou
                if " joined the game" in linha:
                    nome = linha.split("]:")[-1].strip().split(" joined")[0].strip()
                    if nome not in self.players_online:
                        self.players_online.append(nome)
                        print(f"[MC SERVER] Player entrou: {nome}")

                # Player saiu
                elif " left the game" in linha:
                    nome = linha.split("]:")[-1].strip().split(" left")[0].strip()
                    if nome in self.players_online:
                        self.players_online.remove(nome)

                # Crash
                if "Exception in server tick loop" in linha or "FATAL" in linha:
                    print(f"[MC SERVER ERRO] {linha[:200]}")
        except Exception as e:
            print(f"[MC SERVER LOG] erro: {e}")

    def parar(self):
        if not self.esta_rodando() and not self.processo:
            return False, "Servidor ja esta parado."

        try:
            # Envia 'stop' via stdin (saida limpa)
            if self.processo and self.processo.stdin:
                try:
                    self.processo.stdin.write("stop\n")
                    self.processo.stdin.flush()
                except: pass

            # Aguarda 10s
            for _ in range(10):
                if not self.esta_rodando():
                    break
                time.sleep(1)

            # Forca se ainda rodando
            if self.esta_rodando():
                matar_servidor()

            self.rodando = False
            self.processo = None
            self.players_online = []
            return True, "Servidor parado, Sir."
        except Exception as e:
            return False, f"Erro: {e}"

    def status(self):
        rodando = self.esta_rodando()
        uptime = 0
        if self.iniciado_em:
            uptime = int(time.time() - self.iniciado_em)
        return {
            "rodando": rodando,
            "uptime_seg": uptime,
            "players": list(self.players_online),
            "qtd_players": len(self.players_online),
            "porta": SERVER_PORT,
        }

    def status_texto(self):
        s = self.status()
        if not s["rodando"]:
            return "Servidor Minecraft offline, Sir."
        h = s["uptime_seg"] // 3600
        m = (s["uptime_seg"] % 3600) // 60
        msg = f"Servidor online ha {h}h {m}m. "
        if s["qtd_players"] > 0:
            msg += f"{s['qtd_players']} jogadores: {', '.join(s['players'][:5])}."
        else:
            msg += "Sem jogadores conectados."
        return msg


_instance = None


def get_server(callback_voz=None):
    global _instance
    if _instance is None:
        _instance = MinecraftServer(callback_voz=callback_voz)
    return _instance
