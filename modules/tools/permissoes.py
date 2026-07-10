# -*- coding: utf-8 -*-
"""
JARVIS Sistema de Permissoes v2 - 5 niveis
N1-N3: auto | N4: confirma 1x | N5: confirma 2x
Arquivos do JARVIS sempre Nivel 5.
"""

import time
import threading
from pathlib import Path


PATH_JARVIS = "C:\\Users\\Administrator\\Desktop\\JARVIS"


NIVEIS = {
    # NIVEL 1 - leitura
    "listar_pasta":      1,
    "ler_arquivo":       1,
    "espaco_disco":      1,
    "listar_drives":     1,
    "buscar_arquivos":   1,
    "analisar_codigo":   1,

    # NIVEL 2 - escrita nova
    "criar_codigo":      2,
    "criar_arquivo":     2,
    "escrever_texto":    2,

    # NIVEL 3 - automacao
    "mover_arquivo":     3,
    "copiar_arquivo":    3,
    "organizar_pasta":   3,
    "renomear_arquivo":  3,
    "organizar_downloads": 3,
    "enviar_pelo_discord": 3,

    # NIVEL 4 - sistema
    "abrir_programa":    3,
    "fechar_programa":   3,
    "modificar_arquivo": 4,
    "rodar_comando":     4,
    "reiniciar_jarvis":  4,

    # NIVEL 5 - critico (sempre dupla confirmacao)
    "deletar_arquivo":   5,
    "deletar_pasta":     5,
    "instalar_programa": 5,
    "executar_shell":    5,
}


def _eh_arquivo_jarvis(caminho):
    """Checa se arquivo pertence ao projeto JARVIS."""
    if not caminho:
        return False
    try:
        p = str(Path(caminho).resolve()).upper()
        return p.startswith(PATH_JARVIS.upper())
    except Exception:
        return False


class GerenciadorPermissoes:
    def __init__(self):
        self.pendente = None
        self.timeout_seg = 60
        self.lock = threading.Lock()

    def get_nivel(self, ferramenta, args=None):
        """
        Retorna nivel. Se for modificar arquivo do JARVIS, forca Nivel 5.
        """
        nivel_base = NIVEIS.get(ferramenta, 4)

        # PROTECAO ESPECIAL: arquivos do JARVIS sempre N5
        if args and ferramenta in ("modificar_arquivo", "criar_arquivo", "deletar_arquivo"):
            caminho = args.get("caminho") or args.get("destino") or ""
            if _eh_arquivo_jarvis(caminho):
                return 5

        return nivel_base

    def precisa_confirmar(self, ferramenta, args=None):
        return self.get_nivel(ferramenta, args) >= 4

    def iniciar_confirmacao(self, ferramenta, args, fala_executar):
        nivel = self.get_nivel(ferramenta, args)
        with self.lock:
            self.pendente = {
                "ferramenta": ferramenta,
                "args": args,
                "fala_executar": fala_executar,
                "etapa": 1,
                "nivel": nivel,
                "ts": time.time(),
            }
        if nivel == 4:
            return f"Sir, vou {fala_executar}. Confirma com 'sim'?"
        else:
            extra = ""
            if args:
                caminho = args.get("caminho") or args.get("destino") or ""
                if _eh_arquivo_jarvis(caminho):
                    extra = " ATENCAO: e um arquivo do proprio JARVIS."
            return f"Sir,{extra} vou {fala_executar}. Confirma com 'sim'?"

    def tem_pendente(self):
        with self.lock:
            if not self.pendente:
                return False
            if time.time() - self.pendente["ts"] > self.timeout_seg:
                self.pendente = None
                return False
            return True

    def processar_resposta(self, texto):
        with self.lock:
            if not self.pendente:
                return (None, None)

            resposta = texto.lower().strip()
            confirma_1 = any(w == resposta or resposta.startswith(w + " ") for w in
                            ["sim", "claro", "pode", "vai", "manda", "executa", "faz"])
            confirma_2 = "confirmo" in resposta
            nega = any(w == resposta or resposta.startswith(w + " ") for w in
                      ["nao", "não", "cancela", "para", "esquece"])

            pend = self.pendente

            if nega:
                self.pendente = None
                return ("cancelado", "Cancelado, Sir.")

            if pend["nivel"] == 4:
                if confirma_1:
                    dados = dict(pend)
                    self.pendente = None
                    return ("executar", dados)
                return (None, None)

            if pend["nivel"] == 5:
                if pend["etapa"] == 1:
                    if confirma_1:
                        pend["etapa"] = 2
                        pend["ts"] = time.time()
                        return ("pergunta",
                                "Tem certeza, Sir? Confirma de novo com 'confirmo'.")
                    return (None, None)
                elif pend["etapa"] == 2:
                    if confirma_2:
                        dados = dict(pend)
                        self.pendente = None
                        return ("executar", dados)
                    if confirma_1:
                        return ("pergunta",
                                "Sir, preciso da palavra exata 'confirmo'.")
                    return (None, None)

        return (None, None)

    def cancelar(self):
        with self.lock:
            self.pendente = None


_instance = None

def get_permissoes():
    global _instance
    if _instance is None:
        _instance = GerenciadorPermissoes()
    return _instance
