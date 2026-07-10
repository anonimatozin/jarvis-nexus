# -*- coding: utf-8 -*-
"""
JARVIS Gerenciador de Conversa Multi-Turno v1.0
Mantem estado de conversas pendentes.
Ex: JARVIS pergunta "do que se trata?", aguarda resposta.
"""

import time
import threading


class GerenciadorConversa:
    def __init__(self):
        self.estado_pendente = None  # dict com info do que ta aguardando
        self.timestamp = 0
        self.timeout_seg = 90  # se nao responder em 90s, esquece
        self.lock = threading.Lock()

    def aguardar_resposta(self, tipo, contexto, callback=None):
        """
        Marca que JARVIS fez pergunta e espera resposta.

        tipo: 'codigo_aula', 'confirmar_organizar', 'qual_arquivo', etc
        contexto: dict com info acumulada
        callback: funcao a chamar quando resposta vier
        """
        with self.lock:
            self.estado_pendente = {
                "tipo": tipo,
                "contexto": contexto,
                "callback": callback,
                "ts": time.time(),
            }
            self.timestamp = time.time()
        print(f"[CONVERSA] Aguardando resposta tipo={tipo}")

    def tem_pendente(self):
        """Tem conversa aguardando resposta?"""
        with self.lock:
            if not self.estado_pendente:
                return False
            # Expirou?
            if time.time() - self.timestamp > self.timeout_seg:
                print("[CONVERSA] Pendencia expirou")
                self.estado_pendente = None
                return False
            return True

    def get_pendente(self):
        """Retorna info da pendencia atual."""
        with self.lock:
            return self.estado_pendente

    def consumir(self, resposta_usuario):
        """
        Consome a pendencia com a resposta.
        Retorna (tipo, contexto_atualizado, callback)
        """
        with self.lock:
            if not self.estado_pendente:
                return None, None, None
            pendente = self.estado_pendente
            # Adiciona resposta no contexto
            ctx = dict(pendente["contexto"])
            ctx["ultima_resposta"] = resposta_usuario
            ctx["historico"] = ctx.get("historico", []) + [resposta_usuario]
            self.estado_pendente = None
            return pendente["tipo"], ctx, pendente.get("callback")

    def limpar(self):
        with self.lock:
            self.estado_pendente = None
            self.timestamp = 0


_instance = None

def get_conversa():
    global _instance
    if _instance is None:
        _instance = GerenciadorConversa()
    return _instance
