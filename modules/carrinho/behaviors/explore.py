"""
Explore - Exploracao inteligente do ambiente.
Usa varredura do servo pra escolher melhor direcao.
"""

import time
import random
from .base import Behavior
from .. import config as cfg


class Explore(Behavior):
    nome = "explore"
    descricao = "Explora ambiente desviando inteligentemente"

    def executar(self, carrinho):
        print("[EXPLORE] Iniciado.")
        
        if not cfg.HC_SR04_INSTALADO:
            print("[EXPLORE] Precisa HC-SR04!")
            return

        passos = 0

        while not self.parar_se_solicitado(carrinho):
            passos += 1
            
            # A cada 5 passos, faz varredura completa
            if passos % 5 == 0:
                print("[EXPLORE] Varrendo ambiente...")
                leituras = carrinho.varrer_ambiente()
                if leituras:
                    melhor_ang = max(leituras, key=leituras.get)
                    melhor_dist = leituras[melhor_ang]
                    print(f"[EXPLORE] Melhor caminho: {melhor_ang}° ({melhor_dist}cm)")
                    
                    # Vira pra direcao mais livre
                    if melhor_ang < 60:
                        carrinho.movement.direita(tempo_ms=400)
                    elif melhor_ang > 120:
                        carrinho.movement.esquerda(tempo_ms=400)
                    
                    if not self.dormir(0.6, carrinho):
                        break

            # Avanca verificando
            dist = carrinho.distancia(angulo=cfg.SERVO_ANGULO_FRENTE)
            
            if dist and dist > cfg.DISTANCIA_SEGURA_CM:
                carrinho.movement.frente(tempo_ms=500)
                if not self.dormir(0.6, carrinho):
                    break
            else:
                # Obstaculo - decide rapido
                carrinho.movement.parar()
                escolha = random.choice(["esq", "dir"])
                if escolha == "esq":
                    carrinho.movement.esquerda(tempo_ms=500)
                else:
                    carrinho.movement.direita(tempo_ms=500)
                if not self.dormir(0.7, carrinho):
                    break

        carrinho.movement.parar()
        print("[EXPLORE] Parado.")
