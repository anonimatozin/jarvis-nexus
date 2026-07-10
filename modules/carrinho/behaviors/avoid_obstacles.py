"""
Avoid Obstacles - anda pra frente desviando.
PRECISA do HC-SR04 instalado.
"""

import time
from .base import Behavior
from .. import config as cfg


class AvoidObstacles(Behavior):
    nome = "avoid_obstacles"
    descricao = "Anda pra frente e desvia de obstaculos"

    def executar(self, carrinho):
        print("[AVOID] Iniciado.")
        
        if not cfg.HC_SR04_INSTALADO:
            print("[AVOID] HC-SR04 nao instalado em config.py!")
            return

        while not self.parar_se_solicitado(carrinho):
            # Le distancia frontal
            dist = carrinho.distancia(angulo=cfg.SERVO_ANGULO_FRENTE)
            
            if dist is None:
                print("[AVOID] Sem leitura, esperando...")
                if not self.dormir(0.5, carrinho):
                    break
                continue

            print(f"[AVOID] Frente: {dist}cm")

            if dist > cfg.DISTANCIA_SEGURA_CM:
                # Caminho livre, vai pra frente
                carrinho.movement.frente(tempo_ms=400)
                if not self.dormir(0.5, carrinho):
                    break
            else:
                # Obstaculo! Para e olha pros lados
                carrinho.movement.parar()
                time.sleep(0.3)
                print(f"[AVOID] Obstaculo a {dist}cm! Analisando...")

                # Olha esquerda
                dist_esq = carrinho.distancia(angulo=cfg.SERVO_ANGULO_ESQ)
                time.sleep(0.3)
                # Olha direita
                dist_dir = carrinho.distancia(angulo=cfg.SERVO_ANGULO_DIR)
                time.sleep(0.3)
                # Volta servo pra frente
                carrinho.wifi.servo(cfg.SERVO_ANGULO_FRENTE)

                print(f"[AVOID] ESQ:{dist_esq} DIR:{dist_dir}")

                # Decide: vai pro lado mais livre
                if dist_esq is None: dist_esq = 0
                if dist_dir is None: dist_dir = 0

                if max(dist_esq, dist_dir) < cfg.DISTANCIA_SEGURA_CM:
                    # Sem saida! da re e gira
                    print("[AVOID] Sem saida, dando re")
                    carrinho.movement.tras(tempo_ms=600)
                    if not self.dormir(0.8, carrinho):
                        break
                    carrinho.movement.direita(tempo_ms=800)
                    if not self.dormir(1.0, carrinho):
                        break
                elif dist_esq > dist_dir:
                    print("[AVOID] Virando esquerda")
                    carrinho.movement.esquerda(tempo_ms=600)
                    if not self.dormir(0.8, carrinho):
                        break
                else:
                    print("[AVOID] Virando direita")
                    carrinho.movement.direita(tempo_ms=600)
                    if not self.dormir(0.8, carrinho):
                        break

        carrinho.movement.parar()
        print("[AVOID] Parado.")
