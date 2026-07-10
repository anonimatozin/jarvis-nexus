"""
Random Walk - anda aleatorio (cuidado: vai bater!)
Use apenas em espaco aberto sem sensor.
"""

import random
import time
from .base import Behavior


class RandomWalk(Behavior):
    nome = "random_walk"
    descricao = "Anda aleatoriamente (sem desviar)"

    def executar(self, carrinho):
        print("[RANDOM] Iniciado. Cuidado, vai bater!")
        
        while not self.parar_se_solicitado(carrinho):
            # Escolhe acao aleatoria
            acao = random.choice([
                "frente", "frente", "frente",  # mais peso pra ir reto
                "esquerda", "direita",
            ])
            tempo = random.randint(500, 1500)

            if acao == "frente":
                carrinho.movement.frente(tempo_ms=tempo)
            elif acao == "esquerda":
                carrinho.movement.esquerda(tempo_ms=random.randint(300, 700))
            elif acao == "direita":
                carrinho.movement.direita(tempo_ms=random.randint(300, 700))

            # Pausa
            if not self.dormir(tempo/1000.0 + 0.3, carrinho):
                break

        carrinho.movement.parar()
        print("[RANDOM] Parado.")
