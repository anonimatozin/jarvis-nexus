"""
Patrol - Patrulha vai-e-volta numa area.
"""

import time
from .base import Behavior
from .. import config as cfg


class Patrol(Behavior):
    nome = "patrol"
    descricao = "Patrulha vai e volta"

    def executar(self, carrinho):
        print("[PATROL] Iniciado.")
        
        ciclos = 0

        while not self.parar_se_solicitado(carrinho):
            ciclos += 1
            print(f"[PATROL] Ciclo {ciclos}")

            # Anda pra frente ate achar obstaculo
            distancia_total = 0
            while distancia_total < 5 and not self.parar_se_solicitado(carrinho):
                if cfg.HC_SR04_INSTALADO:
                    dist = carrinho.distancia()
                    if dist and dist < cfg.DISTANCIA_SEGURA_CM:
                        print(f"[PATROL] Obstaculo a {dist}cm, voltando.")
                        break
                
                carrinho.movement.frente(tempo_ms=500)
                if not self.dormir(0.6, carrinho):
                    return
                distancia_total += 1

            # Para e gira 180
            carrinho.movement.parar()
            time.sleep(0.3)
            print("[PATROL] Girando 180°")
            carrinho.movement.direita(tempo_ms=1200)
            if not self.dormir(1.5, carrinho):
                break

        carrinho.movement.parar()
        print("[PATROL] Parado.")
