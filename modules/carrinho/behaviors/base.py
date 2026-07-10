"""
Behavior base - todos os modos herdam disso.
"""

import time


class Behavior:
    """Comportamento autonomo base."""

    nome = "base"
    descricao = "Comportamento base"

    def executar(self, carrinho):
        """Override em subclasses. carrinho = CarrinhoController."""
        raise NotImplementedError

    def parar_se_solicitado(self, carrinho):
        """Verifica se foi pedido pra parar."""
        return not carrinho.behavior_running

    def dormir(self, segundos, carrinho):
        """Sleep que pode ser interrompido."""
        ini = time.time()
        while time.time() - ini < segundos:
            if self.parar_se_solicitado(carrinho):
                return False
            time.sleep(0.1)
        return True
