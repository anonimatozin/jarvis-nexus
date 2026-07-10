"""
J.A.R.V.I.S. - Motor v23.0
Mudancas:
  - Wake word OBRIGATORIO em toda frase (sem conversa continua)
  - Modulo clima integrado
  - Localizacao automatica criptografada
  - Brain com historico de conversa
"""

import os
import sys
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=ResourceWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)
import re
import time
import uuid
import threading
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import USER_NAME, JARVIS_NAME
from core.brain import JarvisBrain
from output.tts_engine import TTSEngine
from modules.system_control import SystemControl
from modules.app_launcher_inteligente import AppLauncherInteligente
from modules.aprendizado import Aprendizado
from modules.tarefas_compostas import TarefasCompostas
from modules.pesquisa_web import PesquisaWeb
from modules.scheduler import Scheduler
from memory.database import JarvisMemory
from utils.logger import (
    setup_logger, print_jarvis, print_system,
    print_success, print_error, print_banner, print_user,
)

try:
    from memoria.semantic import MemoriaSemantica
    MEM_SEM_OK = True
except ImportError:
    MEM_SEM_OK = False

try:
    from modules.context_detector import ContextDetector
    CTX_OK = True
except ImportError:
    CTX_OK = False

try:
    from discord_bot.bot import JarvisDiscord
    DISCORD_OK = True
except ImportError:
    DISCORD_OK = False

# NOVO
try:
    from modules.clima import get_clima_atual, get_previsao, falar_clima_atual, falar_previsao
    CLIMA_OK = True
except ImportError:
    CLIMA_OK = False

try:
    from modules.localizacao import (
        get_localizacao, get_cidade_atual, garantir_localizacao,
        detectar_e_salvar, mudar_cidade_manual
    )
    LOC_OK = True
except ImportError:
    LOC_OK = False

try:
    from modules.visual.gerenciador import get_memoria_visual
    VISUAL_OK = True
except ImportError as e:
    print(f"[VISUAL] indisponivel: {e}")
    VISUAL_OK = False

# HYBRID VOICE (online + offline PT-BR)
try:
    from modules.audio.hybrid_voice import HybridVoice, get_hybrid_voice
    HYBRID_VOICE_OK = True
except ImportError:
    HYBRID_VOICE_OK = False

try:
    from modules.capacidades import listar_tudo, falar_resumo
    CAP_OK = True
except ImportError:
    CAP_OK = False

try:
    from modules.notificacoes import notify_jarvis_online
    NOTIF_OK = True
except ImportError:
    NOTIF_OK = False

try:
    from modules.minecraft.manager import get_minecraft
    MC_OK = True
except ImportError:
    MC_OK = False

try:
    from modules.minecraft.legion import get_legion
    LEGION_OK = True
except ImportError:
    LEGION_OK = False

try:
    from modules.minecraft.server import get_server as get_mc_server
    MC_SERVER_OK = True
except ImportError:
    MC_SERVER_OK = False

try:
    from modules.esp32.server import get_esp32_server
    ESP32_OK = True
except ImportError:
    ESP32_OK = False

from modules.nlu.router import NLURouter


try:
    from modules.luzes import get_luzes
    LUZES_OK = True
except ImportError:
    LUZES_OK = False

try:
    from modules.produtividade import get_produtividade
    PROD_OK = True
except ImportError:
    PROD_OK = False

try:
    from modules.celular import get_celular
    CEL_OK = True
except ImportError:
    CEL_OK = False

try:
    from modules.tv_samsung import get_tv
    TV_OK = True
except ImportError:
    TV_OK = False

try:
    from modules.seguranca import get_seguranca
    SEG_OK = True
except ImportError:
    SEG_OK = False

try:
    from modules.entretenimento import get_entretenimento
    ENT_OK = True
except ImportError:
    ENT_OK = False

try:
    from modules.cameras import get_cameras
    CAM_OK = True
except ImportError:
    CAM_OK = False


from modules.nlu.intent_classifier import carregar_aprendizados

logger = setup_logger("engine")


class JarvisEngine:

    def __init__(self, use_voice_input=True, use_voice_output=True, interaction_mode="hybrid"):
        self.running = False
        self.use_voice_input = use_voice_input
        self.use_voice_output = use_voice_output
        self.interaction_mode = interaction_mode
        self.session_id = str(uuid.uuid4())[:8]

        self._last_response = ""
        self._last_response_time = 0.0
        self._last_input = ""
        self._last_input_time = 0.0
        self._respond_lock = threading.Lock()
        self._process_lock = threading.Lock()

        self.brain = None
        self.tts = None
        self.speech = None
        self.visao = None
        self.aprendizado = None
        self.app_launcher = None
        self.system_control = None
        self.memory = None
        self.memoria_sem = None
        self.tarefas = None
        self.pesquisa = None
        self.scheduler = None
        self.context = None
        self.discord_bot = None
        self.hud = None
        self.memoria_visual = None
        self.nlu_router = None
        self.minecraft = None
        self.esp32 = None
        self.legion = None
        self.mc_server = None
        self.cameras = None
        self.luzes = None
        self.produtividade = None
        self.celular = None
        self.tv = None
        self.seguranca = None
        self.entretenimento = None
        self.dev_agent = None
        self.intencao = None
        self.conversa = None

        print_system("Inicializando J.A.R.V.I.S. NEXUS v23.0...")
        self._boot_subsystems()
        self._garantir_localizacao_inicial()
        print_success("Todos os modulos prontos.")
        try:
            if NOTIF_OK:
                notify_jarvis_online()
        except Exception:
            pass

    def _garantir_localizacao_inicial(self):
        """Detecta localizacao no primeiro boot."""
        if not LOC_OK:
            return
        try:
            loc = get_localizacao()
            if not loc:
                print_system("  > Detectando localizacao via IP...")
                loc = garantir_localizacao()
                if loc:
                    print_success(f"    Localizacao: {loc.get('cidade', '?')} (criptografada)")
        except Exception as e:
            print_error(f"    Localizacao: {e}")

    def _boot_subsystems(self):
        try:
            print_system("  > Cerebro (IA)...")
            self.brain = JarvisBrain()
            print_success("    Cerebro online.")
        except Exception as e:
            print_error(f"    Cerebro falhou: {e}")

        # HYBRID VOICE (online + offline)
        self.hybrid_voice = None
        if HYBRID_VOICE_OK:
            try:
                print_system("  > Voz Hybrid (online + offline)...")
                self.hybrid_voice = get_hybrid_voice()
                print_success("    Voz hybrid ativa.")
            except Exception as e:
                print_error(f"    Voz hybrid falhou: {e}")

        if self.use_voice_output:
            try:
                print_system("  > Voz (TTS)...")
                if self.hybrid_voice:
                    self.tts = self.hybrid_voice  # Usa hybrid como tts
                else:
                    self.tts = TTSEngine()
                print_success("    Voz online.")
            except Exception as e:
                print_error(f"    Voz falhou: {e}")

        try:
            print_system("  > Aprendizado...")
            self.aprendizado = Aprendizado()
            print_success("    Aprendizado ativo.")
        except Exception as e:
            print_error(f"    Aprendizado falhou: {e}")

        try:
            print_system("  > Controle do PC...")
            self.system_control = SystemControl()
            self.app_launcher = AppLauncherInteligente()
            self.memory = JarvisMemory()
            print_success("    Sistema operacional.")
        except Exception as e:
            print_error(f"    Sistema falhou: {e}")

        try:
            print_system("  > Rotinas...")
            self.tarefas = TarefasCompostas(
                app_launcher=self.app_launcher,
                system_control=self.system_control,
            )
            print_success("    Rotinas online.")
        except Exception as e:
            print_error(f"    Rotinas falharam: {e}")

        try:
            print_system("  > Pesquisa...")
            self.pesquisa = PesquisaWeb(brain=self.brain)
            print_success("    Pesquisa online.")
        except Exception as e:
            print_error(f"    Pesquisa falhou: {e}")

        if MEM_SEM_OK:
            try:
                print_system("  > Memoria semantica...")
                self.memoria_sem = MemoriaSemantica()
                if self.memoria_sem.disponivel:
                    s = self.memoria_sem.estatisticas()
                    print_success(f"    Memoria online ({s.get('total',0)}).")
            except Exception as e:
                print_error(f"    Memoria falhou: {e}")

        try:
            print_system("  > Scheduler...")
            self.scheduler = Scheduler(
                callback_fala=self._respond,
                system_control=self.system_control,
            )
            self.scheduler.iniciar()
            print_success("    Scheduler online.")
        except Exception as e:
            print_error(f"    Scheduler falhou: {e}")

        if CTX_OK:
            try:
                print_system("  > Context detector...")
                self.context = ContextDetector()
                if self.context.disponivel:
                    self.context.iniciar()
                    print_success("    Context online.")
            except Exception as e:
                print_error(f"    Context falhou: {e}")

        if DISCORD_OK:
            try:
                print_system("  > Discord...")
                self.discord_bot = JarvisDiscord(engine_ref=self)
                if self.discord_bot.iniciar():
                    print_success("    Discord iniciando.")
            except Exception as e:
                print_error(f"    Discord falhou: {e}")

        try:
            print_system("  > Visao...")
            from perception.visao import Visao
            self.visao = Visao()
            print_success("    Visao online.")
        except Exception as e:
            print_system(f"    Visao indisponivel: {e}")

        if self.use_voice_input:
            try:
                print_system("  > Microfone (STT)...")
                if self.hybrid_voice:
                    # Hybrid voice já inclui STT offline (Vosk)
                    self.speech = self.hybrid_voice  # Usa hybrid como speech
                    print_success("    Microfone hybrid (online + offline).")
                else:
                    from input.speech_recognition_engine import SpeechEngine
                    self.speech = SpeechEngine()
                    if self.speech.is_available():
                        print_success("    Microfone online.")
                    else:
                        self.speech = None
            except Exception as e:
                print_error(f"    Microfone falhou: {e}")
                self.speech = None


        # MEMORIA VISUAL (a cada 2min)
        if VISUAL_OK:
            try:
                print_system("  > Memoria visual...")
                self.memoria_visual = get_memoria_visual(
                    callback_voz=self._respond
                )
                self.memoria_visual.iniciar()
                print_success("    Memoria visual ativa (captura a cada 2min).")
            except Exception as e:
                print_error(f"    Memoria visual falhou: {e}")


        # NLU Router
        try:
            print_system("  > NLU Router...")
            self.nlu_router = NLURouter(self)
            qtd = carregar_aprendizados()
            if qtd > 0:
                print_success(f"    NLU ativo ({qtd} aprendizados).")
            else:
                print_success("    NLU ativo.")
        except Exception as e:
            print_error(f"    NLU falhou: {e}")


        # MINECRAFT BOT
        if MC_OK:
            try:
                print_system("  > Minecraft bot manager...")
                self.minecraft = get_minecraft(callback_voz=self._respond)
                print_success("    Minecraft pronto (diga 'Jarvis entra no minecraft').")
            except Exception as e:
                print_error(f"    Minecraft falhou: {e}")

        # MC SERVER (Paper local)
        if MC_SERVER_OK:
            try:
                print_system("  > MC Server manager...")
                self.mc_server = get_mc_server(callback_voz=self._respond)
                print_success("    Servidor MC pronto (diga 'Jarvis liga servidor').")
            except Exception as e:
                print_error(f"    MC Server falhou: {e}")

        # LEGIAO DE FERRO
        if LEGION_OK:
            try:
                print_system("  > Legion manager...")
                def display_legiao(txt):
                    if self.esp32:
                        try: self.esp32.mostrar_texto(txt, duracao_seg=10)
                        except: pass
                self.legion = get_legion(
                    callback_voz=self._respond,
                    callback_display=display_legiao,
                )
                print_success("    Legiao de Ferro pronta (diga 'Jarvis cria legiao de 10').")
            except Exception as e:
                print_error(f"    Legion falhou: {e}")


        # CAMERAS IP
        if CAM_OK:
            try:
                print_system("  > Cameras IP...")
                def popup_camera(dados):
                    if self.hud and self.hud.window:
                        try:
                            self.hud.window.sig_camera.emit(dados)
                        except: pass
                self.cameras = get_cameras(
                    callback_voz=self._respond,
                    callback_popup=popup_camera,
                )
                qtd = len(self.cameras.listar())
                print_success(f"    Cameras prontas ({qtd} configuradas).")
            except Exception as e:
                print_error(f"    Cameras falhou: {e}")

        # ESP32 Jarvis Deck
        if ESP32_OK:
            try:
                print_system("  > ESP32 Jarvis Deck...")
                def callback_esp32_cmd(cmd):
                    # Processa comando vindo do keypad/palmas
                    try:
                        resposta = self.processar(cmd)
                        if resposta:
                            self._respond(resposta)
                    except Exception as e:
                        print_error(f"[ESP32 CMD] {e}")

                self.esp32 = get_esp32_server(
                    callback_voz=self._respond,
                    callback_comando=callback_esp32_cmd,
                )
                self.esp32.iniciar()
                ip = self.esp32.ip_local
                print_success(f"    ESP32 server em ws://{ip}:8766")
            except Exception as e:
                print_error(f"    ESP32 falhou: {e}")



        # LUZES TUYA
        if LUZES_OK:
            try:
                print_system("  > Luzes (Tuya)...")
                from modules.luzes import get_luzes
                self.luzes = get_luzes(callback_voz=self._respond)
                qtd = len(self.luzes.listar()) if hasattr(self.luzes, "listar") else 0
                print_success(f"    Luzes prontas ({qtd} configuradas).")
            except Exception as e:
                print_error(f"    Luzes falhou: {e}")

        # ═══ PRODUTIVIDADE ═══
        if PROD_OK:
            try:
                print_system("  > Produtividade...")
                self.produtividade = get_produtividade(
                    context_detector=self.context,
                    memory=self.memory,
                    brain=self.brain,
                )
                self.produtividade.iniciar_tracking()
                print_success("    Produtividade ativa.")
            except Exception as e:
                print_error(f"    Produtividade falhou: {e}")

        # ═══ CELULAR ═══
        if CEL_OK:
            try:
                print_system("  > Celular Android...")
                self.celular = get_celular()
                if self.celular.connected:
                    print_success("    Celular conectado.")
                else:
                    print_error("    Celular não conectado (verifique ADB)")
            except Exception as e:
                print_error(f"    Celular falhou: {e}")

        # ═══ TV SAMSUNG ═══
        if TV_OK:
            try:
                print_system("  > TV Samsung SmartThings...")
                self.tv = get_tv()
                if self.tv.api.token:
                    print_success("    TV SmartThings pronta.")
                else:
                    print_error("    TV sem token SmartThings")
            except Exception as e:
                print_error(f"    TV falhou: {e}")

        # ═══ SEGURANCA ═══
        if SEG_OK:
            try:
                print_system("  > Seguranca...")
                self.seguranca = get_seguranca()
                print_success("    Seguranca ativa.")
            except Exception as e:
                print_error(f"    Seguranca falhou: {e}")

        # ═══ ENTRETENIMENTO ═══
        if ENT_OK:
            try:
                print_system("  > Entretenimento...")
                self.entretenimento = get_entretenimento(brain=self.brain)
                print_success("    Entretenimento ativo.")
            except Exception as e:
                print_error(f"    Entretenimento falhou: {e}")

        # ═══ SELF-EVOLVING SKILLS ═══
        try:
            print_system("  > Skills auto-evolutivas...")
            from modules.skills import get_skill_evolver
            self.skills = get_skill_evolver()
            print_success(f"    Skills prontas ({len(self.skills._skills)} carregadas).")
        except Exception as e:
            print_error(f"    Skills falhou: {e}")
            self.skills = None

        # ═══ PROACTIVE AUTONOMY ═══
        try:
            print_system("  > Proactive Autonomy...")
            from modules.autonomy import get_proactive_engine
            self.autonomia = get_proactive_engine()
            print_success("    Autonomia pronta.")
        except Exception as e:
            print_error(f"    Autonomia falhou: {e}")
            self.autonomia = None

        # ═══ SAFETY TIERS ═══
        try:
            print_system("  > Safety Tiers...")
            from modules.security import get_safety_tiers
            self.safety = get_safety_tiers()
            print_success("    Safety pronta.")
        except Exception as e:
            print_error(f"    Safety falhou: {e}")
            self.safety = None

        # ═══ GOAL PURSUIT (OKR) ═══
        try:
            print_system("  > Goal Pursuit...")
            from modules.productivity import get_goal_pursuit
            self.goals = get_goal_pursuit()
            print_success(f"    Goals prontos ({len(self.goals.goals)} objetivos).")
        except Exception as e:
            print_error(f"    Goals falhou: {e}")
            self.goals = None

        # ═══ DEV AGENT (OpenCode integrado) ═══
        try:
            print_system("  > Dev Agent (OpenCode)...")
            from modules.dev_agent import get_dev_agent
            self.dev_agent = get_dev_agent(
                callback_voz=self._respond,
                brain=self.brain,
            )
            status = "OpenCode OK" if self.dev_agent.opencode_ok else "so brain"
            print_success(f"    Dev Agent pronto ({status}).")
        except Exception as e:
            print_error(f"    Dev Agent falhou: {e}")
            self.dev_agent = None

        # ═══ ANALISADOR DE INTENCAO NATURAL ═══
        try:
            print_system("  > Analisador de Intencao...")
            from modules.intencao import get_analisador, get_conversa
            self.intencao = get_analisador(brain=self.brain)
            self.conversa = get_conversa()
            print_success("    Intencao natural pronta.")
        except Exception as e:
            print_error(f"    Intencao falhou: {e}")
            self.intencao = None
            self.conversa = None


        # ═══ TOOL EXECUTOR (Brain decide ferramentas) ═══
        try:
            print_system("  > Tool Executor (Brain agent)...")
            from modules.tools import get_executor
            self.tool_executor = get_executor(
                brain=self.brain,
                dev_agent=self.dev_agent,
                callback_voz=self._respond,
                engine=self,
            )
            print_success("    Tool Executor pronto.")
        except Exception as e:
            print_error(f"    Tool Executor falhou: {e}")
            self.tool_executor = None

        # ═══ JARVIS TURBO (Central de Comando) ═══
        try:
            print_system("  > Jarvis Turbo (central de comando)...")
            from modules.turbo import get_turbo
            self.turbo = get_turbo(engine=self)
            print_success("    Turbo pronto.")
        except Exception as e:
            print_error(f"    Turbo falhou: {e}")
            self.turbo = None


    def _show_popup(self, tipo, **kwargs):
        """Notificacao flutuante INDEPENDENTE do HUD (estilo Windows).
        Thread-safe via signal.
        """
        if not self.hud or not self.hud.window:
            print(f"[POPUP] sem hud, ignorando tipo={tipo}")
            return
        win = self.hud.window
        print(f"[POPUP NOTIF] tipo={tipo}")
        try:
            win.sig_popup.emit(tipo, dict(kwargs))
        except Exception as ex:
            print(f"[POPUP] erro emit: {ex}")

    def _on_fala_terminou(self):
        """Chamado quando TTS termina - fecha popup auto se for clima/status."""
        try:
            if self.hud and self.hud.window:
                notif = getattr(self.hud.window, "popup_notif", None)
                if notif and hasattr(notif, "fechar_se_auto_voz"):
                    # Precisa rodar na thread Qt
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(0, notif.fechar_se_auto_voz)
        except Exception as e:
            print(f"[POPUP voz fim] erro: {e}")

    def set_hud(self, hud_launcher):
        self.hud = hud_launcher
        try:
            self._plugar_botoes_hud()
            print("[ENGINE] HUD plugado e conectado.")
        except Exception as e:
            print(f"[ENGINE] erro plugar HUD: {e}")

    def _plugar_botoes_hud(self):
        try:
            if not self.hud or not self.hud.window:
                return
            w = self.hud.window

            def novo_mic():
                w.control_bar.mic_muted = not w.control_bar.mic_muted
                w.control_bar.btn_mic.setProperty("muted", "true" if w.control_bar.mic_muted else "false")
                w.control_bar.btn_mic.style().unpolish(w.control_bar.btn_mic)
                w.control_bar.btn_mic.style().polish(w.control_bar.btn_mic)
                if self.speech:
                    self.speech.set_mutado(w.control_bar.mic_muted)
                if w.control_bar.mic_muted:
                    w.control_bar.set_status("MICROFONE MUTADO")
                else:
                    w.control_bar.set_status("AGUARDANDO  ·  diga 'Jarvis'")

            try:
                w.control_bar.sig_toggle_mic.disconnect()
            except (TypeError, RuntimeError):
                pass
            w.control_bar.sig_toggle_mic.connect(novo_mic)

            def novo_pause():
                if self.tts:
                    try:
                        self.tts.parar()
                    except Exception:
                        pass
                w.reset_idle()
            try:
                w.control_bar.sig_pause_tts.disconnect()
            except (TypeError, RuntimeError):
                pass
            w.control_bar.sig_pause_tts.connect(novo_pause)


            def toggle_capture():
                if self.memoria_visual:
                    if w.control_bar.capture_paused:
                        self.memoria_visual.pausar()
                    else:
                        self.memoria_visual.retomar()
            try:
                w.control_bar.sig_toggle_capture.disconnect()
            except (TypeError, RuntimeError):
                pass
            w.control_bar.sig_toggle_capture.connect(toggle_capture)

            print_success("    Botoes do HUD conectados.")
        except Exception as e:
            print_error(f"    Plugar botoes: {e}")

    def _hud_set_state(self, state):
        if self.hud:
            try:
                self.hud.set_orb_state(state)
            except Exception:
                pass
        # NOVO: tambem manda pro ESP32
        if self.esp32:
            try:
                self.esp32.set_estado(state)
            except Exception:
                pass

    def _hud_show(self):
        if self.hud:
            try:
                self.hud.show_from_wake()
            except Exception:
                pass

    def set_interaction_mode(self, mode):
        if mode not in ("voice", "text", "hybrid"):
            return False
        self.interaction_mode = mode
        return True

    def start(self):
        import random
        self.running = True

        frases_inicio = [
            "Pronto pra servir, Sir.",
            "Como posso ajudar, Sir?",
            "Estou online, Sir. O que precisa?",
            "Sistemas operacionais. Como posso ajudar?",
            "Todos os sistemas online, Sir.",
            "A disposicao, Sir.",
            "O que deseja, Sir?",
            "Pronto. Como posso ajudar?",
            "Online e operacional, Sir.",
            "Em que posso ajudar, Sir?",
        ]
        self._respond(random.choice(frases_inicio))
        print_system("")
        print_system("=" * 60)
        print_system(f"  Modo: {self.interaction_mode.upper()}")
        print_system(f"  HUD Qt: ativo")
        print_system(f"  Wake word: 'Jarvis' EM TODA FRASE")
        print_system(f"  Exemplo: 'Jarvis que horas sao'")
        print_system("=" * 60)
        print_system("")

        if self.speech and self.interaction_mode in ("voice", "hybrid"):
            threading.Thread(target=self._voice_loop, daemon=True).start()

        self._terminal_input_loop()

    def _terminal_input_loop(self):
        while self.running:
            try:
                texto = input(f"\n  + {USER_NAME}: ").strip()
                if not self.running:
                    break
                if not texto:
                    continue
                if texto.lower().strip() in ("sair", "exit", "quit"):
                    self.shutdown()
                    break
                resposta = self.processar(texto)
                if resposta:
                    self._respond(resposta)
            except KeyboardInterrupt:
                self.shutdown()
                break
            except EOFError:
                break
            except Exception:
                time.sleep(0.5)

    def _voice_loop(self):
        """Loop de voz com proteção total contra crashes."""
        print_system("Wake word ativo. Diga 'Jarvis <comando>' para falar.")
        self._hud_set_state("idle")

        consecutive_errors = 0
        MAX_ERRORS = 5

        while self.running:
            try:
                if self.interaction_mode not in ("voice", "hybrid"):
                    time.sleep(1)
                    continue

                if not self.speech:
                    time.sleep(2)
                    continue

                try:
                    comando, original = self.speech.listen_with_wake(
                        timeout=5, phrase_time_limit=15
                    )
                except Exception as e:
                    consecutive_errors += 1
                    print_error(f"[VOZ] STT erro: {e}")
                    if consecutive_errors >= MAX_ERRORS:
                        print_error("[VOZ] muitos erros consecutivos, pausa 10s")
                        time.sleep(10)
                        consecutive_errors = 0
                    else:
                        time.sleep(1)
                    continue

                consecutive_errors = 0

                if comando is None:
                    continue

                # Detectou wake word
                try:
                    self._hud_show()
                except Exception:
                    pass

                # So saudacao
                if comando == "":
                    self._hud_set_state("listening")
                    self._respond("Sim, Sir?")
                    self._hud_set_state("idle")
                    continue

                # Comandos de encerrar
                tl = comando.lower().strip()
                if tl in ("encerrar", "tchau", "sair", "desligar", "fechar"):
                    self._respond("Encerrando, Sir.")
                    time.sleep(1.5)
                    self.shutdown()
                    os._exit(0)

                # Processa
                try:
                    self._hud_set_state("thinking")
                    resposta = self.processar(comando)
                    if resposta:
                        self._respond(resposta)
                except Exception as e:
                    print_error(f"[VOZ] processar erro: {e}")
                    self._respond("Tive um problema, Sir. Pode repetir?")
                finally:
                    self._hud_set_state("idle")

            except Exception as e:
                print_error(f"[VOZ LOOP] {e}")
                import traceback
                traceback.print_exc()
                time.sleep(2)

        print_system("[VOZ] Loop encerrado.")

    def processar(self, texto, from_hud=False):
        if not texto:
            return ""
        with self._process_lock:
            now = time.time()
            if texto == self._last_input and (now - self._last_input_time) < 1.0:
                return ""
            self._last_input = texto
            self._last_input_time = now

            if not from_hud:
                print_user(texto)

            if self.aprendizado:
                try:
                    self.aprendizado.aprender(texto)
                except Exception:
                    pass

            if self.memoria_sem and self.memoria_sem.disponivel:
                threading.Thread(
                    target=self._auto_aprender, args=(texto,), daemon=True
                ).start()

            return self._rotear_comando(texto)

    def _auto_aprender(self, texto):
        if not self.memoria_sem or not self.memoria_sem.disponivel:
            return
        tl = texto.lower()
        gatilhos = [
            "meu nome", "eu sou ", "me chamo", "meu aniversario",
            "eu moro", "moro em", "eu trabalho", "trabalho com",
            "eu gosto", "eu adoro", "meu favorito", "minha favorita",
            "vou comprar", "preciso de", "meu amigo", "meu pai",
            "minha mae", "meu canal", "meu projeto",
        ]
        for g in gatilhos:
            if g in tl:
                try:
                    cat = self.memoria_sem.detectar_categoria(texto)
                    self.memoria_sem.lembrar(texto, cat)
                except Exception:
                    pass
                break

    def _rotear_comando(self, texto):
        """Roteamento via NLU."""
        if self.nlu_router:
            try:
                return self.nlu_router.rotear(texto)
            except Exception as e:
                print_error(f"[NLU] {e}")
        # Fallback se NLU nao disponivel
        if self.brain:
            try:
                return self.brain.think(texto)
            except Exception as e:
                return f"Erro: {e}"
        return "Nao entendi."

    def _respond(self, texto):
        if not texto:
            return
        with self._respond_lock:
            now = time.time()
            if texto == self._last_response and (now - self._last_response_time) < 2.0:
                return
            self._last_response = texto
            self._last_response_time = now

        print_jarvis(texto)
        self._hud_set_state("speaking")

        # Mostra numero relevante no display do deck
        if self.esp32:
            try:
                self.esp32.extrair_numero_display(texto)
            except Exception:
                pass

        if self.tts and self.use_voice_output:
            try:
                self.tts.speak(texto)
            except Exception:
                pass

        # NOVO: se a resposta for uma pergunta, ativa modo pendente
        if self.speech and texto.rstrip().endswith("?"):
            try:
                self.speech.ativar_pendente()
            except Exception:
                pass

        self._hud_set_state("idle")

    def responder(self, texto):
        self._respond(texto)

    def shutdown(self):
        import random
        if not self.running:
            return
        self.running = False

        frases_saida = [
            "Ate logo, Sir.",
            "Ate breve, Sir.",
            "Encerrando. Ate mais, Sir.",
            "Sistemas desligando. Ate logo, Sir.",
            "Pronto. Ate quando precisar, Sir.",
        ]
        try:
            self._respond(random.choice(frases_saida))
        except:
            pass
        print_system("Encerrando subsistemas...")
        for nome, obj, metodo in [
            ("memoria_visual", self.memoria_visual, "parar"),
            ("legion", self.legion, "parar_tudo"),
            ("minecraft", self.minecraft, "parar_bot"),
            ("esp32", self.esp32, "parar"),
            ("scheduler", self.scheduler, "parar"),
            ("context", self.context, "parar"),
            ("visao", self.visao, "fechar"),
            ("brain", self.brain, "shutdown"),
            ("memory", self.memory, "close"),
            ("tts", self.tts, "cleanup"),
            ("discord", self.discord_bot, "parar"),
            ("produtividade", self.produtividade, "parar_tracking"),
        ]:
            if obj and hasattr(obj, metodo):
                try:
                    getattr(obj, metodo)()
                except:
                    pass
        print_success("J.A.R.V.I.S. offline.")