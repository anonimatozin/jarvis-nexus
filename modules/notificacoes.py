"""
Notificacoes Windows (toast nativo).
"""
import threading

try:
    from win10toast import ToastNotifier
    TOAST_OK = True
    _toaster = ToastNotifier()
except ImportError:
    TOAST_OK = False
    _toaster = None


def notify(titulo, mensagem, duracao=5):
    """Mostra notificacao Windows nao bloqueante."""
    if not TOAST_OK or not _toaster:
        return

    def show():
        try:
            _toaster.show_toast(
                titulo,
                mensagem,
                duration=duracao,
                threaded=False,
            )
        except Exception as e:
            print(f"[NOTIF] {e}")

    threading.Thread(target=show, daemon=True).start()


def notify_jarvis_online():
    notify(
        "J.A.R.V.I.S. Online",
        "Sistema iniciado. Diga 'Jarvis' para começar.",
        duracao=4,
    )


def notify_pendrive_status(conectado):
    if conectado:
        notify("Pendrive Conectado", "Memoria visual sincronizada.", duracao=3)
    else:
        notify("Pendrive Removido", "Modo cache ativo.", duracao=3)
