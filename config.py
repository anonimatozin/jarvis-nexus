# config.py
"""
J.A.R.V.I.S. - Configuração Global do Sistema
Todas as configurações centralizadas para fácil manutenção.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Carrega variáveis do arquivo .env
load_dotenv()

# ===== CAMINHOS =====
BASE_DIR = Path(__file__).resolve().parent
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "interface" / "assets"

# Criar diretórios se não existirem
MEMORY_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ===== IDENTIDADE =====
JARVIS_NAME = os.getenv("JARVIS_NAME", "Jarvis")
USER_NAME = os.getenv("USER_NAME", "Sir")
WAKE_WORD = os.getenv("WAKE_WORD", "jarvis").lower()
LANGUAGE = os.getenv("LANGUAGE", "pt-BR")

# ===== IA =====
AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")  # "groq" ou "openai"
AI_MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ===== VOZ =====
TTS_VOICE = os.getenv("TTS_VOICE", "pt-BR-AntonioNeural")
TTS_RATE = "+10%"  # Velocidade da fala
TTS_VOLUME = "+0%"  # Volume da fala

# ===== SISTEMA =====
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DATABASE_PATH = MEMORY_DIR / "jarvis_memory.db"

# ===== VERSÃO =====
VERSION = "1.0.0-alpha"
CODENAME = "Genesis"

# ──────────────────────────────────────────────────────────────────
#  MODOS DE INTERAÇÃO (NEXUS)
# ──────────────────────────────────────────────────────────────────

import json

SETTINGS_FILE = Path(__file__).parent / "data" / "settings.json"

DEFAULT_SETTINGS = {
    "interaction_mode": "hybrid",   # "voice" | "text" | "hybrid"
    "theme": "cyan",                 # "cyan" | "orange"
    "auto_start": False,
    "hud_always_on_top": True,
    "voice_output_enabled": True,
    "wake_on_launch": True,
    "animation_intensity": "high",   # "low" | "medium" | "high"
}

def load_settings() -> dict:
    """Carrega settings.json ou cria defaults."""
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Garante todas as chaves
            for k, v in DEFAULT_SETTINGS.items():
                data.setdefault(k, v)
            return data
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict) -> bool:
    """Persiste settings.json."""
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False