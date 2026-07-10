"""Configuracoes do HUD v3.0 - Stark Reactor Pro."""
import json
import os
from pathlib import Path

# ═══ PALETA "STARK REACTOR PRO" ═══
PALETA = {
    "bg_main":      "#06090f",
    "bg_panel":     "#0c1018",
    "bg_elevated":  "#111822",
    "bg_card":      "#151d28",
    "border":       "#1a2535",
    "border_hover": "#243040",
    "border_focus": "#2a7fff",

    "text_muted":   "#3d5570",
    "text_dim":     "#5a7a95",
    "text_main":    "#8aaccc",
    "text_bright":  "#c0daf0",
    "text_white":   "#eaf2fb",

    "accent":       "#2a7fff",
    "accent_dim":   "#1a5fcc",
    "accent_glow":  "#4da6ff",
    "accent_bg":    "#0d1f3a",

    "orb_idle":     "#2a7fff",
    "orb_listen":   "#00c8ff",
    "orb_think":    "#8b5cf6",
    "orb_speak":    "#06b6d4",

    "success":      "#10b981",
    "warning":      "#f59e0b",
    "danger":       "#ef4444",
    "info":         "#3b82f6",
}

# ═══ JANELA ═══
TITLE_BAR_HEIGHT = 36
CONTROL_BAR_HEIGHT = 100
CONFIG_PANEL_WIDTH = 380

# ═══ ORB ═══
ORB_MIN_SIZE = 120
ORB_MAX_SIZE = 400
ORB_DEFAULT_RATIO = 0.35

# ═══ MINI-ORB ═══
MINI_ORB_SIZE = 140

# ═══ AUTO-MINIMIZE ═══
DEFAULT_IDLE_TIMEOUT = 30

# ═══ POPUP ═══
POPUP_WIDTH = 480
POPUP_HEIGHT = 340

# ═══ SETTINGS FILE ═══
SETTINGS_FILE = Path("data/hud_settings.json")

_default_settings = {
    "ultimo_tamanho": [1000, 700],
    "ultima_posicao": [100, 100],
    "ultimo_estado": "fullscreen",
    "mic_mutado": False,
    "tts_mutado": False,
    "iniciar_com_windows": False,
    "iniciar_minimizado": False,
    "auto_show_on_wake": True,
    "auto_minimize_idle": True,
    "idle_timeout_seconds": 30,
    "tts_volume": 80,
    "tts_voice": "pt-BR-AntonioNeural",
    "tts_speed": 1.0,
    "mic_device": "default",
    "mic_sensitivity": 50,
    "wake_word": "jarvis",
    "wake_timeout": 10,
    "ai_provider": "auto",
    "ai_temperature": 0.7,
    "mini_orb_position": [None, None],
}

_cache = None

def load_settings():
    global _cache
    if _cache is not None:
        return _cache
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = _default_settings.copy()
                merged.update(data)
                _cache = merged
                return _cache
    except Exception:
        pass
    _cache = _default_settings.copy()
    return _cache

def save_settings(settings=None):
    global _cache
    if settings is None:
        settings = _cache
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        _cache = settings
    except Exception as e:
        print(f"[HUD] erro save settings: {e}")

def get(key, default=None):
    s = load_settings()
    return s.get(key, default)

def set_value(key, value):
    s = load_settings()
    s[key] = value
    save_settings(s)
