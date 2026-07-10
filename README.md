# J.A.R.V.I.S. NEXUS v24.0

Just A Rather Very Intelligent System

## Rodar

    .\venv\Scripts\Activate.ps1
    python main.py --mode hybrid

Fala 'Jarvis' e da comando.

## Features

### Core
- Voz (TTS/STT com edge-tts, kokoro)
- HUD Qt (interface grafica)
- IA multi-provider (Groq, Gemini, Ollama)
- Wake word detection

### Smart Home
- Controle de luzes (Tuya/ESP32)
- TV Samsung SmartThings
- Celular (Android)
- ESP32 Deck

### Novos Modulos (v24.0)
- **Screen Vision** - OCR em tempo real, leitura de tela
- **Desktop Tools** - 31 ferramentas de controle (mouse, teclado, midia, clipboard)
- **Autonomy Engine** - Self-learning avancado, prediz proximo comando
- **Facial Recognition** - Autenticacao por rosto
- **Emergency Response** - Monitoramento critico do sistema
- **Context Manager** - Sliding window com auto-resumo

### Outros
- Discord Bot
- Bot Minecraft
- Scheduler/agendamentos
- Seguranca/criptografia
- Pesquisa web
- Memoria persistente

## Documentacao

- docs/PROMPT_CONTINUACAO.txt - Pra nova IA continuar
- docs/ROADMAP.md - Proximas features
- modules/capacidades.py - Todos comandos

## Configuracao

.env:
    GROQ_API_KEY=gsk_xxxxx
    DISCORD_TOKEN=xxxxx (opcional)

## Novos Modulos

### Screen Vision
    from modules.vision.screen_vision import ScreenVision
    vision = ScreenVision()
    vision.ocr_screen()
    vision.click_on_text("OK")

### Desktop Tools
    from modules.tools.desktop_tools import DesktopTools
    tools = DesktopTools()
    tools.media_play_pause()
    tools.get_system_info()

### Autonomy Engine
    from modules.autonomy.autonomy_engine import AutonomyEngine
    engine = AutonomyEngine()
    engine.register_command("abrir chrome")
    engine.predict_next_command()

### Facial Recognition
    from modules.security.facial_recognition import FacialRecognition
    face = FacialRecognition()
    face.register_face("Sir")
    face.authenticate()

### Emergency Response
    from modules.monitoring.emergency import EmergencyResponse
    emergency = EmergencyResponse()
    emergency.get_health_report()

---
Versao: 24.0 (2026-07-08)
