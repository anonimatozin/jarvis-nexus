"""
Digitador automatico humanizado.
Simula teclado real com delays, acentos via tecla morta.
Para imediatamente se mouse for movido (anti-deteccao).
"""
import time
import random
import threading

try:
    import keyboard
    KB_OK = True
except ImportError:
    KB_OK = False

try:
    from pynput.mouse import Listener as MouseListener
    MOUSE_OK = True
except ImportError:
    MOUSE_OK = False


# Mapa de acentos para tecla morta
ACENTOS = {
    'a': ("'", 'a'), 'e': ("'", 'e'), 'i': ("'", 'i'), 'o': ("'", 'o'), 'u': ("'", 'u'),
    'A': ("'", 'A'), 'E': ("'", 'E'), 'I': ("'", 'I'), 'O': ("'", 'O'), 'U': ("'", 'U'),
    'a': ('`', 'a'), 'e': ('`', 'e'), 'i': ('`', 'i'), 'o': ('`', 'o'), 'u': ('`', 'u'),
    'A': ('`', 'A'), 'E': ('`', 'E'), 'I': ('`', 'I'), 'O': ('`', 'O'), 'U': ('`', 'U'),
    'a': ('^', 'a'), 'e': ('^', 'e'), 'i': ('^', 'i'), 'o': ('^', 'o'), 'u': ('^', 'u'),
    'A': ('^', 'A'), 'E': ('^', 'E'), 'I': ('^', 'I'), 'O': ('^', 'O'), 'U': ('^', 'U'),
    'a': ('~', 'a'), 'o': ('~', 'o'), 'n': ('~', 'n'),
    'A': ('~', 'A'), 'O': ('~', 'O'), 'N': ('~', 'N'),
    'c': ('c', None), 'C': ('C', None),
}


class Digitador:
    """Digita texto simulando humano. Para se mouse mover."""

    def __init__(self):
        self.cancelar = False
        self._mouse_inicial = None
        self._listener = None

    def _on_mouse_move(self, x, y):
        if self._mouse_inicial is None:
            self._mouse_inicial = (x, y)
            return
        # Se moveu mais que 30px, cancela
        dx = abs(x - self._mouse_inicial[0])
        dy = abs(y - self._mouse_inicial[1])
        if dx + dy > 30:
            print("[DIGITADOR] Mouse movido - cancelando!")
            self.cancelar = True
            return False  # para listener

    def _digitar_letra(self, letra):
        if letra in ACENTOS:
            acento, base = ACENTOS[letra]
            if base is None:
                keyboard.write(acento)
            else:
                keyboard.write(acento)
                time.sleep(0.02)
                keyboard.write(base)
        else:
            keyboard.write(letra)

    def digitar(self, texto: str, delay_inicial: int = 5,
                vel_min: float = 0.04, vel_max: float = 0.10) -> bool:
        """
        Digita o texto inteiro.
        Args:
            texto: o que digitar
            delay_inicial: segundos pra voce clicar no campo
            vel_min/max: range do delay entre teclas
        Returns:
            True se completou, False se cancelado
        """
        if not KB_OK:
            print("[DIGITADOR] keyboard nao instalado")
            return False

        print(f"[DIGITADOR] {len(texto)} caracteres em ~{(len(texto)*0.08)/60:.1f}min")
        print(f"[DIGITADOR] Clique no campo. {delay_inicial}s...")

        for i in range(delay_inicial, 0, -1):
            print(f"  {i}...")
            time.sleep(1)

        # Inicia listener do mouse
        self.cancelar = False
        self._mouse_inicial = None
        if MOUSE_OK:
            self._listener = MouseListener(on_move=self._on_mouse_move)
            self._listener.start()

        print("[DIGITADOR] Comecou. Mexa o mouse pra cancelar.")

        try:
            for letra in texto:
                if self.cancelar:
                    print("[DIGITADOR] Cancelado pelo usuario.")
                    return False

                self._digitar_letra(letra)

                if letra in '.!?':
                    time.sleep(0.35)
                elif letra in ',;:':
                    time.sleep(0.18)
                elif letra == ' ':
                    time.sleep(0.12)
                elif letra == '\n':
                    time.sleep(0.30)
                else:
                    time.sleep(random.uniform(vel_min, vel_max))

            print("[DIGITADOR] Concluido!")
            return True
        finally:
            if self._listener:
                self._listener.stop()
