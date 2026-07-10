"""
J.A.R.V.I.S. Control Center - Backend API
Centro de comando completo via Flask.
"""
import os
import sys
import json
import time
import psutil
import socket
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

app = Flask(__name__, static_folder="static")

LOGS_FILE = ROOT / "data" / "dashboard_logs.json"
MEMORY_FILE = ROOT / "memory" / "jarvis_memory.db"
CHAT_HISTORY = []

def save_log(entry):
    logs = []
    if LOGS_FILE.exists():
        try:
            logs = json.loads(LOGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            logs = []
    logs.append(entry)
    if len(logs) > 500:
        logs = logs[-500:]
    LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOGS_FILE.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")

# ══════════════════════════════════════════
#  SYSTEM DATA
# ══════════════════════════════════════════

def get_ping():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        start = time.time()
        s.connect(("8.8.8.8", 53))
        latency = round((time.time() - start) * 1000)
        s.close()
        return latency
    except Exception:
        return 0

def get_uptime():
    boot = datetime.fromtimestamp(psutil.boot_time())
    delta = datetime.now() - boot
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    mins, _ = divmod(rem, 60)
    return f"{days}d {hours}h {mins}m"

def get_jarvis_status():
    return {
        "name": "J.A.R.V.I.S.",
        "version": "2.0.0",
        "codename": "Nexus",
        "state": "idle",
        "provider": os.getenv("AI_PROVIDER", "groq"),
        "model": os.getenv("AI_MODEL", "llama-3.3-70b-versatile"),
        "language": "pt-BR",
        "platform": sys.platform,
    }

def get_modules():
    modules_dir = ROOT / "modules"
    mods = []
    if modules_dir.exists():
        for item in sorted(modules_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("_"):
                py_files = list(item.glob("*.py"))
                mods.append({
                    "name": item.name,
                    "files": len(py_files),
                    "active": len(py_files) > 0,
                })
    return mods

# ══════════════════════════════════════════
#  ROUTES - STATIC
# ══════════════════════════════════════════

@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "server": "JARVIS Dashboard", "time": datetime.now().isoformat()})

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

# ══════════════════════════════════════════
#  ROUTES - DASHBOARD
# ══════════════════════════════════════════

@app.route("/api/dashboard")
def api_dashboard():
    cpu = psutil.cpu_percent(interval=0.3)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/")
    net = psutil.net_io_counters()
    freq = psutil.cpu_freq()

    return jsonify({
        "time": datetime.now().strftime("%H:%M:%S"),
        "date": datetime.now().strftime("%d/%m/%Y"),
        "uptime": get_uptime(),
        "cpu": {
            "percent": cpu,
            "cores": psutil.cpu_count(),
            "freq": round(freq.current, 0) if freq else 0,
        },
        "ram": {
            "percent": mem.percent,
            "used": round(mem.used / (1024**3), 2),
            "total": round(mem.total / (1024**3), 2),
        },
        "disk": {
            "percent": disk.percent,
            "used": round(disk.used / (1024**3), 2),
            "total": round(disk.total / (1024**3), 2),
            "free": round(disk.free / (1024**3), 2),
        },
        "network": {
            "ping": get_ping(),
            "sent_mb": round(net.bytes_sent / (1024**2), 2),
            "recv_mb": round(net.bytes_recv / (1024**2), 2),
        },
        "jarvis": get_jarvis_status(),
        "modules_count": len(get_modules()),
    })

# ══════════════════════════════════════════
#  ROUTES - CHAT
# ══════════════════════════════════════════

@app.route("/api/chat", methods=["GET"])
def api_chat_get():
    return jsonify({"history": CHAT_HISTORY[-50:]})

@app.route("/api/chat", methods=["POST"])
def api_chat_post():
    data = request.json or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"error": "empty message"}), 400

    user_msg = {"role": "user", "content": msg, "time": datetime.now().strftime("%H:%M")}
    CHAT_HISTORY.append(user_msg)

    save_log({"type": "chat_user", "message": msg, "time": user_msg["time"]})

    response = process_command(msg)

    jarvis_msg = {"role": "jarvis", "content": response, "time": datetime.now().strftime("%H:%M")}
    CHAT_HISTORY.append(jarvis_msg)

    save_log({"type": "chat_jarvis", "message": response, "time": jarvis_msg["time"]})

    return jsonify({"response": response, "time": jarvis_msg["time"]})

def process_command(msg):
    lower = msg.lower().strip()

    if any(w in lower for w in ["horas", "hora", "que hora"]):
        return f"Agora sao {datetime.now().strftime('%H:%M:%S')}."

    if any(w in lower for w in ["data", "dia", "hoje"]):
        return f"Hoje e {datetime.now().strftime('%d/%m/%Y')}."

    if "status" in lower and ("pc" in lower or "sistema" in lower):
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        return f"CPU: {cpu}% | RAM: {mem.percent}% ({round(mem.used/(1024**3),1)}GB)"

    if "uptime" in lower or "ligado" in lower:
        return f"Sistema ligado ha {get_uptime()}."

    if any(w in lower for w in ["abrir chrome", "chrome"]):
        try:
            subprocess.Popen(["start", "chrome"], shell=True)
            return "Chrome aberto."
        except Exception:
            return "Erro ao abrir Chrome."

    if any(w in lower for w in ["abrir vs code", "vscode", "code"]):
        try:
            subprocess.Popen(["start", "code"], shell=True)
            return "VS Code aberto."
        except Exception:
            return "Erro ao abrir VS Code."

    if any(w in lower for w in ["abrir steam", "steam"]):
        try:
            subprocess.Popen(["start", "steam"], shell=True)
            return "Steam aberto."
        except Exception:
            return "Erro ao abrir Steam."

    if any(w in lower for w in ["desligar", "shutdown"]):
        return "Use o botao de desligar no painel de Controle do PC por seguranca."

    if any(w in lower for w in ["reiniciar", "restart"]):
        return "Use o botao de reiniciar no painel de Controle do PC por seguranca."

    if any(w in lower for w in ["bloquear", "lock"]):
        try:
            subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
            return "PC bloqueado."
        except Exception:
            return "Erro ao bloquear."

    if any(w in lower for w in ["limpar tela", "limpar", "clear"]):
        return "__CLEAR__"

    if any(w in lower for w in ["memoria", "lembra"]):
        return "Minha memoria esta funcionando. Pode me perguntar qualquer coisa que eu lembro."

    if "quem e voce" in lower or "o que voce" in lower:
        return "Eu sou o J.A.R.V.I.S. - Just A Rather Very Intelligent System. Assistente pessoal criado por Vinicius."

    if any(w in lower for w in ["obrigad", "valeu", "brigad"]):
        return "Disponha, Sir. Estou sempre aqui para ajudar."

    if any(w in lower for w in ["oi", "ola", "bom dia", "boa tarde", "boa noite"]):
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Bom dia"
        elif hour < 18:
            greeting = "Boa tarde"
        else:
            greeting = "Boa noite"
        return f"{greeting}, Sir. Como posso ajudar?"

    try:
        from core.brain import Brain
        brain = Brain()
        return brain.think(msg)
    except Exception as e:
        return f"Processando sua mensagem... (Brain offline: {str(e)[:80]})"

# ══════════════════════════════════════════
#  ROUTES - VOICE
# ══════════════════════════════════════════

@app.route("/api/voice/speak", methods=["POST"])
def api_voice_speak():
    data = request.json or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "no text"}), 400

    save_log({"type": "voice_speak", "text": text, "time": datetime.now().strftime("%H:%M")})

    try:
        import edge_tts
        import asyncio

        async def _speak():
            voice = os.getenv("TTS_VOICE", "pt-BR-AntonioNeural")
            output = ROOT / "data" / "last_speech.mp3"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output))
            return str(output)

        path = asyncio.run(_speak())

        try:
            import pygame
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except Exception:
            pass

        return jsonify({"ok": True, "file": path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/voice/listen", methods=["POST"])
def api_voice_listen():
    save_log({"type": "voice_listen", "time": datetime.now().strftime("%H:%M")})
    return jsonify({"ok": True, "text": "Funcionalidade de reconhecimento via browser em desenvolvimento."})

# ══════════════════════════════════════════
#  ROUTES - PC CONTROL
# ══════════════════════════════════════════

@app.route("/api/control/<action>", methods=["POST"])
def api_control(action):
    actions = {
        "shutdown": lambda: subprocess.Popen(["shutdown", "/s", "/t", "30"]),
        "restart": lambda: subprocess.Popen(["shutdown", "/r", "/t", "30"]),
        "lock": lambda: subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"]),
        "chrome": lambda: subprocess.Popen(["start", "chrome"], shell=True),
        "vscode": lambda: subprocess.Popen(["start", "code"], shell=True),
        "steam": lambda: subprocess.Popen(["start", "steam"], shell=True),
        "notepad": lambda: subprocess.Popen(["start", "notepad"], shell=True),
        "explorer": lambda: subprocess.Popen(["start", "explorer"], shell=True),
        "cmd": lambda: subprocess.Popen(["start", "cmd"], shell=True),
        "taskmgr": lambda: subprocess.Popen(["start", "taskmgr"], shell=True),
    }

    if action in actions:
        try:
            actions[action]()
            log_entry = {"type": "control", "action": action, "time": datetime.now().strftime("%H:%M")}
            save_log(log_entry)
            return jsonify({"ok": True, "action": action})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "unknown action"}), 400

# ══════════════════════════════════════════
#  ROUTES - PROCESSES
# ══════════════════════════════════════════

@app.route("/api/processes")
def api_processes():
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            if info["cpu_percent"] and info["cpu_percent"] > 0:
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"][:35],
                    "cpu": round(info["cpu_percent"], 1),
                    "ram_pct": round(info["memory_percent"], 1),
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return jsonify(procs[:15])

# ══════════════════════════════════════════
#  ROUTES - MEMORY
# ══════════════════════════════════════════

@app.route("/api/memory")
def api_memory():
    memories = []
    mem_file = ROOT / "memory" / "memories.json"
    if mem_file.exists():
        try:
            memories = json.loads(mem_file.read_text(encoding="utf-8"))
        except Exception:
            memories = []

    jarvis_info = {
        "user_name": os.getenv("USER_NAME", "Sir"),
        "jarvis_name": os.getenv("JARVIS_NAME", "Jarvis"),
        "project": "J.A.R.V.I.S. Nexus",
        "language": "Python 3.12",
        "platform": sys.platform,
        "provider": os.getenv("AI_PROVIDER", "groq"),
        "model": os.getenv("AI_MODEL", "llama-3.3-70b-versatile"),
    }

    return jsonify({"info": jarvis_info, "memories": memories})

# ══════════════════════════════════════════
#  ROUTES - LOGS
# ══════════════════════════════════════════

@app.route("/api/logs")
def api_logs():
    if LOGS_FILE.exists():
        try:
            logs = json.loads(LOGS_FILE.read_text(encoding="utf-8"))
            return jsonify({"logs": logs[-100:]})
        except Exception:
            pass
    return jsonify({"logs": []})

# ══════════════════════════════════════════
#  ROUTES - MODULES
# ══════════════════════════════════════════

@app.route("/api/modules")
def api_modules():
    return jsonify(get_modules())

# ══════════════════════════════════════════
#  ROUTES - SETTINGS
# ══════════════════════════════════════════

@app.route("/api/settings", methods=["GET"])
def api_settings_get():
    settings_file = ROOT / "data" / "settings.json"
    defaults = {
        "theme": "cyan",
        "language": "pt-BR",
        "ai_provider": os.getenv("AI_PROVIDER", "groq"),
        "ai_model": os.getenv("AI_MODEL", "llama-3.3-70b-versatile"),
        "wake_word": os.getenv("WAKE_WORD", "jarvis"),
        "tts_voice": os.getenv("TTS_VOICE", "pt-BR-AntonioNeural"),
    }
    if settings_file.exists():
        try:
            data = json.loads(settings_file.read_text(encoding="utf-8"))
            defaults.update(data)
        except Exception:
            pass
    return jsonify(defaults)

@app.route("/api/settings", methods=["POST"])
def api_settings_post():
    data = request.json or {}
    settings_file = ROOT / "data" / "settings.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return jsonify({"ok": True})

# ══════════════════════════════════════════
#  ROUTES - STATS
# ══════════════════════════════════════════

@app.route("/api/stats")
def api_stats():
    logs = []
    if LOGS_FILE.exists():
        try:
            logs = json.loads(LOGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            logs = []

    chat_count = sum(1 for l in logs if l.get("type") == "chat_user")
    voice_count = sum(1 for l in logs if l.get("type") in ("voice_speak", "voice_listen"))
    control_count = sum(1 for l in logs if l.get("type") == "control")

    return jsonify({
        "total_commands": chat_count + voice_count + control_count,
        "chat_commands": chat_count,
        "voice_commands": voice_count,
        "control_commands": control_count,
        "uptime": get_uptime(),
    })


# ══════════════════════════════════════════
#  ROUTES - FILES
# ══════════════════════════════════════════

@app.route("/api/files")
def api_files():
    path = request.args.get("path", str(ROOT))
    p = Path(path)
    if not p.exists():
        p = ROOT

    items = []
    try:
        for item in sorted(p.iterdir()):
            try:
                size = ""
                if item.is_file():
                    s = item.stat().st_size
                    if s > 1024*1024:
                        size = f"{s/(1024*1024):.1f} MB"
                    elif s > 1024:
                        size = f"{s/1024:.1f} KB"
                    else:
                        size = f"{s} B"
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "is_dir": item.is_dir(),
                    "size": size,
                })
            except PermissionError:
                pass
    except PermissionError:
        pass

    return jsonify({
        "current": str(p),
        "parent": str(p.parent) if p.parent != p else None,
        "items": items[:200],
    })


# ══════════════════════════════════════════
#  ROUTES - WEATHER
# ══════════════════════════════════════════

@app.route("/api/weather")
def api_weather():
    try:
        import urllib.request
        url = "https://wttr.in/Cruzeiro+do+Oeste?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        current = data.get("current_condition", [{}])[0]
        return jsonify({
            "temp": current.get("temp_C", "--"),
            "feels_like": current.get("FeelsLikeC", "--"),
            "description": current.get("lang_pt", [{}])[0].get("value", current.get("weatherDesc", [{}])[0].get("value", "")),
            "humidity": current.get("humidity", "--"),
            "wind": current.get("windspeedKmph", "--"),
            "wind_dir": current.get("winddir16Point", ""),
            "visibility": current.get("visibility", "--"),
            "pressure": current.get("pressure", "--"),
        })
    except Exception as e:
        return jsonify({"temp": "--", "description": "Indisponivel", "humidity": "--", "wind": "--"})


if __name__ == "__main__":
    print("=" * 50)
    print("  J.A.R.V.I.S. Control Center v2.0")
    print("  http://localhost:8080")
    print("=" * 50)
    app.run(host="0.0.0.0", port=8080, debug=False)
