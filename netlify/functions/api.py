"""
JARVIS Dashboard - Netlify Serverless Function
Serve a API como function no Netlify.
"""
import os
import sys
import json
import time
import psutil
import socket
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def handler(event, context):
    path = event.get("path", "/")
    method = event.get("httpMethod", "GET")
    qs = event.get("queryStringParameters") or {}

    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    try:
        if path == "/api/health":
            return {"statusCode": 200, "headers": headers, "body": json.dumps({"status": "ok", "server": "JARVIS Dashboard"})}
        elif path == "/api/dashboard":
            return api_dashboard(headers)
        elif path == "/api/weather":
            return api_weather(headers)
        elif path == "/api/stats":
            return api_stats(headers)
        elif path == "/api/processes":
            return api_processes(headers)
        elif path == "/api/modules":
            return api_modules(headers)
        elif path == "/api/memory":
            return api_memory(headers)
        elif path == "/api/logs":
            return api_logs(headers)
        elif path == "/api/settings" and method == "GET":
            return api_settings_get(headers)
        elif path == "/api/settings" and method == "POST":
            body = json.loads(event.get("body") or "{}")
            return api_settings_post(body, headers)
        elif path == "/api/chat" and method == "POST":
            body = json.loads(event.get("body") or "{}")
            return api_chat_post(body, headers)
        elif path.startswith("/api/control/"):
            action = path.split("/")[-1]
            return api_control(action, headers)
        else:
            return {"statusCode": 404, "headers": headers, "body": json.dumps({"error": "not found"})}
    except Exception as e:
        return {"statusCode": 500, "headers": headers, "body": json.dumps({"error": str(e)})}


def api_dashboard(headers):
    cpu = psutil.cpu_percent(interval=0.3)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/")
    net = psutil.net_io_counters()
    freq = psutil.cpu_freq()
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime_delta = datetime.now() - boot
    days = uptime_delta.days
    hours, rem = divmod(uptime_delta.seconds, 3600)
    mins, _ = divmod(rem, 60)

    return {"statusCode": 200, "headers": headers, "body": json.dumps({
        "time": datetime.now().strftime("%H:%M:%S"),
        "date": datetime.now().strftime("%d/%m/%Y"),
        "uptime": f"{days}d {hours}h {mins}m",
        "cpu": {"percent": cpu, "cores": psutil.cpu_count(), "freq": round(freq.current, 0) if freq else 0},
        "ram": {"percent": mem.percent, "used": round(mem.used / (1024**3), 2), "total": round(mem.total / (1024**3), 2)},
        "disk": {"percent": disk.percent, "used": round(disk.used / (1024**3), 2), "total": round(disk.total / (1024**3), 2), "free": round(disk.free / (1024**3), 2)},
        "network": {"ping": 0, "sent_mb": round(net.bytes_sent / (1024**2), 2), "recv_mb": round(net.bytes_recv / (1024**2), 2)},
        "jarvis": {"name": "J.A.R.V.I.S.", "version": "2.0.0", "codename": "Nexus", "state": "idle", "provider": os.getenv("AI_PROVIDER", "groq"), "model": os.getenv("AI_MODEL", "llama-3.3-70b-versatile"), "language": "pt-BR", "platform": sys.platform},
        "modules_count": len(list((ROOT / "modules").iterdir())) if (ROOT / "modules").exists() else 0,
    })}


def api_weather(headers):
    try:
        import urllib.request
        url = "https://wttr.in/Cruzeiro+do+Oeste?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        current = data.get("current_condition", [{}])[0]
        return {"statusCode": 200, "headers": headers, "body": json.dumps({
            "temp": current.get("temp_C", "--"),
            "description": current.get("lang_pt", [{}])[0].get("value", current.get("weatherDesc", [{}])[0].get("value", "")),
            "humidity": current.get("humidity", "--"),
            "wind": current.get("windspeedKmph", "--"),
        })}
    except Exception:
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"temp": "--", "description": "Indisponivel", "humidity": "--", "wind": "--"})}


def api_stats(headers):
    return {"statusCode": 200, "headers": headers, "body": json.dumps({
        "total_commands": 0, "chat_commands": 0, "voice_commands": 0,
        "control_commands": 0, "uptime": "N/A (serverless)",
    })}


def api_processes(headers):
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            if info["cpu_percent"] and info["cpu_percent"] > 0:
                procs.append({"pid": info["pid"], "name": info["name"][:35], "cpu": round(info["cpu_percent"], 1), "ram_pct": round(info["memory_percent"], 1)})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return {"statusCode": 200, "headers": headers, "body": json.dumps(procs[:15])}


def api_modules(headers):
    mods = []
    modules_dir = ROOT / "modules"
    if modules_dir.exists():
        for item in sorted(modules_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("_"):
                py_files = list(item.glob("*.py"))
                mods.append({"name": item.name, "files": len(py_files), "active": len(py_files) > 0})
    return {"statusCode": 200, "headers": headers, "body": json.dumps(mods)}


def api_memory(headers):
    return {"statusCode": 200, "headers": headers, "body": json.dumps({
        "info": {"user_name": os.getenv("USER_NAME", "Sir"), "jarvis_name": os.getenv("JARVIS_NAME", "Jarvis"), "project": "J.A.R.V.I.S. Nexus", "language": "Python 3.12", "platform": sys.platform},
        "memories": [],
    })}


def api_logs(headers):
    return {"statusCode": 200, "headers": headers, "body": json.dumps({"logs": []})}


def api_settings_get(headers):
    return {"statusCode": 200, "headers": headers, "body": json.dumps({
        "theme": "cyan", "language": "pt-BR", "ai_provider": os.getenv("AI_PROVIDER", "groq"),
        "ai_model": os.getenv("AI_MODEL", "llama-3.3-70b-versatile"), "wake_word": "jarvis",
        "tts_voice": "pt-BR-AntonioNeural",
    })}


def api_settings_post(body, headers):
    return {"statusCode": 200, "headers": headers, "body": json.dumps({"ok": True})}


def api_chat_post(body, headers):
    msg = body.get("message", "").strip()
    if not msg:
        return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "empty"})}

    lower = msg.lower()
    if any(w in lower for w in ["horas", "hora"]):
        resp = f"Agora sao {datetime.now().strftime('%H:%M:%S')}."
    elif any(w in lower for w in ["data", "hoje"]):
        resp = f"Hoje e {datetime.now().strftime('%d/%m/%Y')}."
    elif any(w in lower for w in ["oi", "ola", "bom dia", "boa tarde", "boa noite"]):
        h = datetime.now().hour
        g = "Bom dia" if h < 12 else "Boa tarde" if h < 18 else "Boa noite"
        resp = f"{g}, Sir. Como posso ajudar?"
    elif "quem e voce" in lower or "o que voce" in lower:
        resp = "Eu sou o J.A.R.V.I.S. - Just A Rather Very Intelligent System."
    elif any(w in lower for w in ["obrigad", "valeu"]):
        resp = "Disponha, Sir."
    else:
        resp = f"Mensagem recebida: '{msg}'. Estou processando..."

    return {"statusCode": 200, "headers": headers, "body": json.dumps({"response": resp, "time": datetime.now().strftime("%H:%M")})}


def api_control(action, headers):
    actions = {
        "lock": lambda: subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"]),
        "chrome": lambda: subprocess.Popen(["start", "chrome"], shell=True),
        "vscode": lambda: subprocess.Popen(["start", "code"], shell=True),
    }
    if action in actions:
        try:
            actions[action]()
            return {"statusCode": 200, "headers": headers, "body": json.dumps({"ok": True, "action": action})}
        except Exception as e:
            return {"statusCode": 500, "headers": headers, "body": json.dumps({"error": str(e)})}
    return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "unknown action"})}
