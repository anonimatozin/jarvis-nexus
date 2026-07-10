"""
Carrinho - Controller principal
Interface entre Jarvis e o carrinho.
"""

import threading
import time
from . import config as cfg
from .wifi_client import WifiClient
from .safety import SafetyMonitor
from .movement import Movement


class CarrinhoController:
    """Controller principal do carrinho.
    
    Uso:
        carrinho = CarrinhoController()
        if carrinho.conectar():
            carrinho.frente()
            carrinho.ativar_modo("avoid_obstacles")
    """

    def __init__(self, ip=None):
        self.wifi = WifiClient(ip=ip)
        self.safety = SafetyMonitor(self.wifi)
        self.movement = Movement(self.wifi, self.safety)
        
        self.modo_atual = "manual"
        self.behavior_thread = None
        self.behavior_running = False
        
        # Lazy load behaviors
        self.behaviors = {}

    # ════════ CONEXAO ════════

    def conectar(self):
        """Tenta conectar ao ESP32."""
        print(f"[CARRINHO] Tentando conectar em {self.wifi.ip}:{self.wifi.port}...")
        if self.wifi.ping():
            print("[CARRINHO] Online!")
            self.safety.iniciar()
            return True
        else:
            print("[CARRINHO] Offline ou IP errado.")
            return False

    def desconectar(self):
        self.parar_modo()
        self.movement.parar()
        self.safety.parar()

    def online(self):
        return self.wifi.online

    def status(self):
        if not self.wifi.online:
            return "Carrinho offline."
        s = self.wifi.status() or "?"
        return f"Carrinho online em {self.wifi.ip}. Status: {s}. Modo: {self.modo_atual}."

    # ════════ COMANDOS DIRETOS ════════

    def frente(self, tempo_ms=None):
        if not self.wifi.online:
            return "Carrinho offline."
        self.movement.frente(tempo_ms)
        return "Indo pra frente."

    def tras(self, tempo_ms=None):
        if not self.wifi.online:
            return "Carrinho offline."
        self.movement.tras(tempo_ms)
        return "Indo pra tras."

    def esquerda(self, tempo_ms=None):
        if not self.wifi.online:
            return "Carrinho offline."
        self.movement.esquerda(tempo_ms)
        return "Virando esquerda."

    def direita(self, tempo_ms=None):
        if not self.wifi.online:
            return "Carrinho offline."
        self.movement.direita(tempo_ms)
        return "Virando direita."

    def parar(self):
        self.parar_modo()
        if self.wifi.online:
            self.movement.parar()
        return "Carrinho parado."

    def dancar(self):
        if not self.wifi.online:
            return "Carrinho offline."
        threading.Thread(target=self.movement.dancar, daemon=True).start()
        return "Dancando, Sir."

    def distancia(self, angulo=None):
        if not self.wifi.online:
            return None
        return self.wifi.distancia(angulo)

    def varrer_ambiente(self):
        """Varre servo e retorna o que ve."""
        if not self.wifi.online:
            return None
        return self.wifi.varrer()

    # ════════ MODOS AUTONOMOS ════════

    def listar_modos(self):
        return cfg.MODOS_DISPONIVEIS

    def ativar_modo(self, nome_modo):
        """Ativa um modo autonomo."""
        if not self.wifi.online:
            return "Carrinho offline."
        if nome_modo not in cfg.MODOS_DISPONIVEIS:
            return f"Modo '{nome_modo}' nao existe. Disponiveis: {cfg.MODOS_DISPONIVEIS}"
        
        # Para modo atual
        self.parar_modo()
        
        # Lazy load do behavior
        try:
            behavior = self._get_behavior(nome_modo)
            if not behavior:
                return f"Modo '{nome_modo}' nao implementado."
            
            self.behavior_running = True
            self.modo_atual = nome_modo
            
            def run():
                try:
                    behavior.executar(self)
                except Exception as e:
                    print(f"[CARRINHO] Erro modo {nome_modo}: {e}")
                finally:
                    self.behavior_running = False
                    self.modo_atual = "manual"
            
            self.behavior_thread = threading.Thread(target=run, daemon=True, name=f"behavior-{nome_modo}")
            self.behavior_thread.start()
            return f"Modo '{nome_modo}' ativado."
        except Exception as e:
            return f"Erro ao ativar modo: {e}"

    def parar_modo(self):
        """Para o modo autonomo atual."""
        if self.behavior_running:
            self.behavior_running = False
            time.sleep(0.5)
        self.modo_atual = "manual"

    def _get_behavior(self, nome):
        """Carrega behavior sob demanda."""
        if nome in self.behaviors:
            return self.behaviors[nome]
        
        try:
            if nome == "random_walk":
                from .behaviors.random_walk import RandomWalk
                b = RandomWalk()
            elif nome == "avoid_obstacles":
                from .behaviors.avoid_obstacles import AvoidObstacles
                b = AvoidObstacles()
            elif nome == "explore":
                from .behaviors.explore import Explore
                b = Explore()
            elif nome == "patrol":
                from .behaviors.patrol import Patrol
                b = Patrol()
            else:
                return None
            
            self.behaviors[nome] = b
            return b
        except Exception as e:
            print(f"[CARRINHO] erro load behavior {nome}: {e}")
            return None
