"""
NEXUS - Context Detector v1.0
Detecta app em foco, registra atividade.
"""

import os
import time
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

try:
    import win32gui
    import win32process
    import psutil
    WIN_OK = True
except ImportError:
    WIN_OK = False
    print("[CONTEXT] win32gui ou psutil faltando")


APP_NAMES = {
    "code.exe": "VS Code",
    "chrome.exe": "Chrome",
    "msedge.exe": "Edge",
    "firefox.exe": "Firefox",
    "notepad.exe": "Notepad",
    "explorer.exe": "Explorador",
    "discord.exe": "Discord",
    "spotify.exe": "Spotify",
    "steam.exe": "Steam",
    "obs64.exe": "OBS",
    "wt.exe": "Terminal",
    "powershell.exe": "PowerShell",
    "cmd.exe": "CMD",
    "calculatorapp.exe": "Calculadora",
    "javaw.exe": "Java/Minecraft",
    "minecraft.exe": "Minecraft",
    "sklauncher.exe": "SKLauncher",
    "capcut.exe": "CapCut",
    "audacity.exe": "Audacity",
    "telegram.exe": "Telegram",
    "whatsapp.exe": "WhatsApp",
    "vlc.exe": "VLC",
    "python.exe": "Python",
    "pythonw.exe": "Python",
}

APPS_TRABALHO = {"code.exe", "wt.exe", "powershell.exe", "cmd.exe"}
APPS_NAVEGADOR = {"chrome.exe", "msedge.exe", "firefox.exe"}
APPS_JOGO = {"javaw.exe", "minecraft.exe", "sklauncher.exe", "steam.exe"}
APPS_SOCIAL = {"discord.exe", "telegram.exe", "whatsapp.exe"}
APPS_MEDIA = {"spotify.exe", "vlc.exe", "obs64.exe", "capcut.exe", "audacity.exe"}


class ContextDetector:
    """Detecta contexto atual do usuario sem invadir."""

    def __init__(self, persist_dir="data/context"):
        self.disponivel = WIN_OK
        self.running = False
        self.thread = None
        self.persist_dir = persist_dir
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        self.app_atual = None
        self.app_atual_inicio = None
        self.janela_atual = ""
        self.uso_hoje = defaultdict(float)
        self.mudancas_hoje = []
        self.sessao = []

        self._load_today()

    def _today_file(self):
        hoje = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.persist_dir, f"{hoje}.json")

    def _load_today(self):
        try:
            f = self._today_file()
            if os.path.exists(f):
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                self.uso_hoje = defaultdict(float, data.get("uso", {}))
                self.mudancas_hoje = data.get("mudancas", [])
        except Exception as e:
            print(f"[CONTEXT] load: {e}")

    def _save_today(self):
        try:
            f = self._today_file()
            data = {
                "uso": dict(self.uso_hoje),
                "mudancas": self.mudancas_hoje[-200:],
                "atualizado": datetime.now().isoformat(),
            }
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[CONTEXT] save: {e}")

    def _get_active_window(self):
        if not WIN_OK:
            return None, ""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return None, ""
            titulo = win32gui.GetWindowText(hwnd) or ""
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == 0:
                return None, titulo
            try:
                proc = psutil.Process(pid)
                nome = proc.name().lower()
                return nome, titulo
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None, titulo
        except Exception:
            return None, ""

    def iniciar(self):
        if self.running or not self.disponivel:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True, name="context")
        self.thread.start()
        print("[CONTEXT] Iniciado em background.")

    def parar(self):
        self.running = False
        self._save_today()

    def _loop(self):
        ultimo_save = time.time()
        while self.running:
            try:
                app, titulo = self._get_active_window()
                if app and app != self.app_atual:
                    agora = datetime.now()
                    if self.app_atual and self.app_atual_inicio:
                        delta = (agora - self.app_atual_inicio).total_seconds()
                        if delta > 1:
                            self.uso_hoje[self.app_atual] += delta
                    self.mudancas_hoje.append({
                        "de": self.app_atual,
                        "para": app,
                        "titulo": titulo[:80],
                        "quando": agora.isoformat(),
                    })
                    self.sessao.append(app)
                    if len(self.sessao) > 20:
                        self.sessao = self.sessao[-20:]
                    self.app_atual = app
                    self.app_atual_inicio = agora
                    self.janela_atual = titulo

                if time.time() - ultimo_save > 60:
                    if self.app_atual and self.app_atual_inicio:
                        delta = (datetime.now() - self.app_atual_inicio).total_seconds()
                        if delta > 1:
                            self.uso_hoje[self.app_atual] += delta
                            self.app_atual_inicio = datetime.now()
                    self._save_today()
                    ultimo_save = time.time()
            except Exception as e:
                print(f"[CONTEXT] erro loop: {e}")
            time.sleep(5)

    def app_friendly_name(self, processo):
        if not processo:
            return "Desconhecido"
        return APP_NAMES.get(processo.lower(), processo.replace(".exe", "").title())

    def get_atividade_atual(self):
        if not self.app_atual:
            return "Nenhuma atividade detectada ainda."
        nome = self.app_friendly_name(self.app_atual)
        if self.app_atual_inicio:
            delta = (datetime.now() - self.app_atual_inicio).total_seconds()
            if delta < 60:
                tempo = f"{int(delta)} segundos"
            elif delta < 3600:
                tempo = f"{int(delta/60)} minutos"
            else:
                tempo = f"{delta/3600:.1f} horas"
            return f"Voce esta no {nome} ha {tempo}, Sir."
        return f"Voce esta no {nome}, Sir."

    def get_tempo_app(self, processo_alvo):
        total = self.uso_hoje.get(processo_alvo, 0)
        if self.app_atual == processo_alvo and self.app_atual_inicio:
            total += (datetime.now() - self.app_atual_inicio).total_seconds()
        return total

    def get_tempo_app_friendly(self, nome_amigavel):
        nome_low = nome_amigavel.lower()
        for proc, nome in APP_NAMES.items():
            if nome_low in nome.lower() or nome_low in proc.lower():
                seg = self.get_tempo_app(proc)
                if seg < 60:
                    return f"{int(seg)} segundos no {nome}"
                elif seg < 3600:
                    return f"{int(seg/60)} minutos no {nome}"
                else:
                    return f"{seg/3600:.1f} horas no {nome}"
        return f"Nao encontrei tempo de uso para '{nome_amigavel}'."

    def get_top_apps(self, top_n=5):
        uso = dict(self.uso_hoje)
        if self.app_atual and self.app_atual_inicio:
            delta = (datetime.now() - self.app_atual_inicio).total_seconds()
            uso[self.app_atual] = uso.get(self.app_atual, 0) + delta
        ordenado = sorted(uso.items(), key=lambda x: x[1], reverse=True)
        resultado = []
        for proc, seg in ordenado[:top_n]:
            nome = self.app_friendly_name(proc)
            if seg < 60:
                tempo_str = f"{int(seg)}s"
            elif seg < 3600:
                tempo_str = f"{int(seg/60)}min"
            else:
                tempo_str = f"{seg/3600:.1f}h"
            resultado.append({"app": nome, "processo": proc, "tempo_seg": seg, "tempo_str": tempo_str})
        return resultado

    def get_resumo_dia(self):
        top = self.get_top_apps(5)
        if not top:
            return "Nenhuma atividade registrada hoje, Sir."
        total_seg = sum(t["tempo_seg"] for t in top)
        horas = total_seg / 3600
        partes = [f"Hoje voce usou o PC por aproximadamente {horas:.1f} horas."]
        partes.append("Apps principais:")
        for i, t in enumerate(top[:3], 1):
            partes.append(f"{i}. {t['app']} ({t['tempo_str']})")
        cat_tempo = defaultdict(float)
        for proc, seg in self.uso_hoje.items():
            if proc in APPS_TRABALHO:
                cat_tempo["trabalho"] += seg
            elif proc in APPS_JOGO:
                cat_tempo["jogos"] += seg
            elif proc in APPS_NAVEGADOR:
                cat_tempo["navegacao"] += seg
            elif proc in APPS_SOCIAL:
                cat_tempo["social"] += seg
            elif proc in APPS_MEDIA:
                cat_tempo["midia"] += seg
        if cat_tempo:
            cat_top = max(cat_tempo.items(), key=lambda x: x[1])
            partes.append(f"Categoria predominante: {cat_top[0]}.")
        return " ".join(partes)

    def get_mudancas_recentes(self, n=5):
        return self.mudancas_hoje[-n:]

    def get_categoria_atual(self):
        if not self.app_atual:
            return "idle"
        if self.app_atual in APPS_TRABALHO:
            return "trabalho"
        if self.app_atual in APPS_JOGO:
            return "jogo"
        if self.app_atual in APPS_NAVEGADOR:
            return "navegacao"
        if self.app_atual in APPS_SOCIAL:
            return "social"
        if self.app_atual in APPS_MEDIA:
            return "midia"
        return "outro"

    def get_tempo_sem_pausa(self):
        if not self.mudancas_hoje:
            return 0
        agora = datetime.now()
        try:
            primeira = datetime.fromisoformat(self.mudancas_hoje[0]["quando"])
            return int((agora - primeira).total_seconds() / 60)
        except:
            return 0
