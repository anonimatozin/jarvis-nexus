# -*- coding: utf-8 -*-
"""
JARVIS Analisador de Intencao Natural v1.1
Brain analisa frase e retorna JSON com intencao real.
"""

import json
import re


PROMPT_ANALISE = """Voce e um classificador JSON. Sua UNICA tarefa: analisar a frase do Sir e responder UM OBJETO JSON puro.

REGRA CRITICA: Sua resposta deve comecar com { e terminar com }. NADA antes nem depois. SEM markdown. SEM explicacao. SO O JSON.

CATEGORIAS POSSIVEIS:
- "conversa": saudacao, papo casual, pergunta sobre voce
- "tarefa_codigo": criar/modificar codigo ou software pro usuario
- "tarefa_arquivo": mexer em arquivos (mover, organizar, listar pastas)
- "tarefa_sistema": acoes no PC (espaco, drives, status)
- "pergunta_info": pergunta que precisa pesquisa ou conhecimento
- "comando_jarvis": modificar o proprio JARVIS (engine, router, modulos)
- "ambiguo": nao da pra saber o que ele quer

FORMATO OBRIGATORIO:
{"categoria":"X","intencao_clara":true,"precisa_perguntar":false,"pergunta_sugerida":"","acao_sugerida":"","contexto":"resumo"}

EXEMPLOS DE RESPOSTA (SEMPRE JSON PURO):

Sir: "tudo bem?"
{"categoria":"conversa","intencao_clara":true,"precisa_perguntar":false,"pergunta_sugerida":"","acao_sugerida":"responder casual","contexto":"saudacao"}

Sir: "to com preguica de fazer esse codigo da aula"
{"categoria":"tarefa_codigo","intencao_clara":false,"precisa_perguntar":true,"pergunta_sugerida":"Entendi, Sir. Quer que eu faca pra voce? Me conta do que se trata o codigo.","acao_sugerida":"","contexto":"usuario quer ajuda com codigo de aula"}

Sir: "calculadora em python simples"
{"categoria":"tarefa_codigo","intencao_clara":true,"precisa_perguntar":false,"pergunta_sugerida":"","acao_sugerida":"criar_codigo: calculadora em python simples","contexto":"criar calculadora python"}

Sir: "meu pc parece tar cheio"
{"categoria":"tarefa_sistema","intencao_clara":true,"precisa_perguntar":false,"pergunta_sugerida":"","acao_sugerida":"mostrar_espaco_disco","contexto":"checar espaco do PC"}

Sir: "organiza meus downloads"
{"categoria":"tarefa_arquivo","intencao_clara":true,"precisa_perguntar":false,"pergunta_sugerida":"","acao_sugerida":"organizar_downloads","contexto":"organizar pasta downloads"}

Sir: "adiciona um log no shutdown do engine.py"
{"categoria":"comando_jarvis","intencao_clara":true,"precisa_perguntar":false,"pergunta_sugerida":"","acao_sugerida":"modificar_arquivo: engine.py adicionar log shutdown","contexto":"modificar engine"}

LEMBRE: responda APENAS o JSON. Nada mais. Comece com { termine com }."""


class AnalisadorIntencao:
    def __init__(self, brain=None):
        self.brain = brain
        self.disponivel = brain is not None
        print(f"[INTENCAO] Analisador {'pronto' if self.disponivel else 'sem brain'}")

    def analisar(self, frase, contexto_anterior=""):
        if not self.disponivel:
            return self._fallback(frase)

        prompt = f'Analise esta frase do Sir e responda APENAS um JSON puro:\n\n"{frase}"'
        if contexto_anterior:
            prompt = f'Contexto anterior: {contexto_anterior}\n\n{prompt}'

        try:
            resposta = self.brain.think(
                prompt,
                system_extra=PROMPT_ANALISE,
                usar_historico=False,
            )

            resposta = resposta.strip()
            resposta = re.sub(r"^```json\s*", "", resposta)
            resposta = re.sub(r"^```\s*", "", resposta)
            resposta = re.sub(r"\s*```$", "", resposta)

            m = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", resposta, re.DOTALL)
            if m:
                resposta = m.group(0)

            dados = json.loads(resposta)

            # Garante campos minimos
            dados.setdefault("categoria", "conversa")
            dados.setdefault("intencao_clara", True)
            dados.setdefault("precisa_perguntar", False)
            dados.setdefault("pergunta_sugerida", "")
            dados.setdefault("acao_sugerida", "")
            dados.setdefault("contexto", frase[:60])

            return dados

        except json.JSONDecodeError as je:
            print(f"[INTENCAO] JSON invalido: {je}")
            print(f"[INTENCAO] Resposta foi: {resposta[:200]}")
            # Tenta inferir do texto cru
            return self._inferir_da_resposta(resposta, frase)
        except Exception as ex:
            print(f"[INTENCAO] erro: {ex}")
            return self._fallback(frase)

    def _inferir_da_resposta(self, resposta, frase):
        """Se brain mandou texto solto, tenta inferir categoria."""
        tl = (resposta + " " + frase).lower()

        if any(w in tl for w in ["organiz", "arruma", "limpa", "downloads",
                                  "pasta", "arquivo"]):
            return {
                "categoria": "tarefa_arquivo",
                "intencao_clara": True,
                "precisa_perguntar": False,
                "pergunta_sugerida": "",
                "acao_sugerida": "organizar",
                "contexto": frase[:60],
            }
        if any(w in tl for w in ["codigo", "programa", "script", "aula",
                                  "python", "function"]):
            return {
                "categoria": "tarefa_codigo",
                "intencao_clara": False,
                "precisa_perguntar": True,
                "pergunta_sugerida": "Quer que eu faca pra voce, Sir? Me da os detalhes.",
                "acao_sugerida": "",
                "contexto": frase[:60],
            }
        if any(w in tl for w in ["disco", "espaco", "drive", "hd", "memoria"]):
            return {
                "categoria": "tarefa_sistema",
                "intencao_clara": True,
                "precisa_perguntar": False,
                "pergunta_sugerida": "",
                "acao_sugerida": "checar_sistema",
                "contexto": frase[:60],
            }
        return self._fallback(frase)

    def _fallback(self, frase):
        return {
            "categoria": "conversa",
            "intencao_clara": True,
            "precisa_perguntar": False,
            "pergunta_sugerida": "",
            "acao_sugerida": "responder casual",
            "contexto": frase[:60],
        }


_instance = None

def get_analisador(brain=None):
    global _instance
    if _instance is None:
        _instance = AnalisadorIntencao(brain=brain)
    return _instance
