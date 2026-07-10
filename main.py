"""
J.A.R.V.I.S. - Entry point v22.1
HUD Qt na MAIN thread, engine em thread separada.
"""
import sys
import argparse
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.logger import print_banner, print_error, print_success, print_system


def main():
    parser = argparse.ArgumentParser(description='J.A.R.V.I.S.')
    parser.add_argument('--mode', choices=['voice', 'text', 'hybrid'], default='hybrid')
    parser.add_argument('--no-voice', action='store_true')
    parser.add_argument('--text', action='store_true')
    parser.add_argument('--no-hud', action='store_true', help='Roda sem HUD Qt (so terminal)')
    args = parser.parse_args()

    mode = "text" if args.text else args.mode
    use_voice_input = mode in ["voice", "hybrid"]
    use_voice_output = not args.no_voice and mode in ["voice", "hybrid"]

    print_banner()

    from core.engine import JarvisEngine

    # 1. Cria engine (sem iniciar)
    engine = JarvisEngine(
        use_voice_input=use_voice_input,
        use_voice_output=use_voice_output,
        interaction_mode=mode,
    )

    if args.no_hud:
        # Modo sem HUD - so terminal
        print_system("Rodando sem HUD (modo terminal)")
        try:
            engine.start()
        except KeyboardInterrupt:
            engine.shutdown()
        return

    # 2. Cria HUD Qt na MAIN thread
    try:
        from hud_qt.launcher import HudLauncher
    except ImportError as e:
        print_error(f"HUD Qt nao disponivel: {e}")
        print_system("Rodando sem HUD...")
        engine.start()
        return

    print_system("Criando HUD Qt na main thread...")

    def engine_callback(comando):
        """Callback pra Turbo Window + ESP32 Deck - rota mensagens pela engine."""
        if comando == "__SHUTDOWN__":
            try:
                engine.shutdown()
            except Exception:
                pass
            import os
            os._exit(0)

        # Comandos diretos do ESP32 Deck
        if comando == "__wake__":
            engine.set_estado("listening")
            return "Ouvindo..."

        if comando == "__cancelar__":
            engine.set_estado("idle")
            return "Cancelado."

        if comando.startswith("__falar__:"):
            texto = comando.replace("__falar__:", "")
            try:
                engine.output.say(texto)
            except Exception:
                pass
            return texto

        if comando == "__screenshot__":
            try:
                from modules.visual import gerenciador
                g = gerenciador.GerenciadorVisual()
                g.tirar_foto()
            except Exception as e:
                print(f"[DECK] Screenshot erro: {e}")
            return "Screenshot tirado."

        # Roteamento normal via NLU
        try:
            resultado = engine.processar(comando)
            return str(resultado) if resultado else "Sem resposta."
        except Exception as e:
            return f"Erro: {e}"

    hud = HudLauncher(engine_callback=engine_callback)
    hud.create()
    engine.set_hud(hud)

    # 3. Engine roda em thread (terminal loop + wake word loop)
    def rodar_engine():
        try:
            engine.start()
        except Exception as e:
            print_error(f"Engine erro: {e}")
            import traceback
            traceback.print_exc()

    engine_thread = threading.Thread(target=rodar_engine, daemon=True, name="JarvisEngine")
    engine_thread.start()

    print_success("Engine rodando em background. HUD na main thread.")

    # 4. HUD bloqueia na main thread (event loop Qt)
    try:
        hud.run()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            engine.shutdown()
        except Exception:
            pass
        print_system("J.A.R.V.I.S. encerrado.")


if __name__ == "__main__":
    main()
