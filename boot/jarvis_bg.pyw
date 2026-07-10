"""
NEXUS - Launcher em segundo plano (.pyw)
Inicia o Jarvis SEM janela de console.
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

# Suprime prints (nao ha console)
class _NullStream:
    def write(self, *a, **k): pass
    def flush(self): pass

sys.stdout = _NullStream()
sys.stderr = _NullStream()

try:
    from config import load_settings
    from core.engine import JarvisEngine

    s = load_settings()
    mode = s.get("interaction_mode", "hybrid")

    engine = JarvisEngine(
        use_voice_input=(mode in ("voice", "hybrid")),
        use_voice_output=s.get("voice_output_enabled", True),
        interaction_mode=mode,
    )
    engine.start()
except Exception:
    import traceback
    log_path = PROJECT_ROOT / "data" / "logs" / "autostart_error.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(traceback.format_exc())
        f.write("\n")
