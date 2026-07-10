# modules/entretenimento.py
"""
J.A.R.V.I.S. - Módulo de Entretenimento v1.0
Jogos, piadas, recomendações, curiosidades.
"""

import os
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.logger import setup_logger

logger = setup_logger("entretenimento")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


PIADAS = [
    "Por que o programador usa óculos? Porque não consegue C#.",
    "O que o Java disse para o C? Você é void demais.",
    "Por que o JavaScript foi ao médico? Porque tinha muita função sem retorno.",
    "Qual a comida favorita do programador? Spaghetti code.",
    "O que o HTML falou pro CSS? Você sempre me estiliza.",
    "Por que o programador foi preso? Porque fez um loop infinito de crimes.",
    "O que acontece quando você divide por zero? O JavaScript chora.",
    "Por que o Python é lento? Porque fica verificando se é seguro.",
    "O que o C++ disse pro C? Você é básico demais.",
    "Qual o momento mais feliz do programador? Quando o código compila na primeira vez.",
]

CURIOSIDADES = [
    "O primeiro bug foi um inseto real encontrado em um computador Harvard em 1947.",
    "O nome 'Python' não vem da cobra, mas do Monty Python's Flying Circus.",
    "O Google foi originalmente chamado de 'BackRub'.",
    "O primeiro email foi enviado em 1971 por Ray Tomlinson.",
    "A primeira mensagem de texto foi enviada em 1992 e dizia 'Merry Christmas'.",
    "O Windows 1.0 foi lançado em 1985 e custava US$100.",
    "O Amazon começou como uma livraria online em 1994.",
    "O smartphone foi inventado em 1992, antes do iPhone.",
    "O YouTube foi criado porque os fundadores queriam compartilhar vídeos de festa.",
    "O primeiro domínio registrado foi symbolics.com em 1985.",
    "O Instagram foi lançado em 2010 e já tinha 1 milhão de usuários em 2 meses.",
    "O Facebook foi originalmente chamado de 'TheFacebook' e era apenas para estudantes de Harvard.",
    "O Bluetooth foi nomeado após o rei viking Harald Bluetooth.",
    "O WiFi não significa nada - é apenas um nome criado para marketing.",
    "O primeiro tweet foi enviado em 2006 e dizia 'just setting up my twttr'.",
]

FILMES = {
    "acao": [
        "Homem de Ferro (2008)",
        "Os Vingadores (2012)",
        "Batman: O Cavaleiro das Trevas (2008)",
        "John Wick (2014)",
        "Mad Max: Estrada da Fúria (2015)",
        "Duna (2021)",
        "Homem-Aranha: Sem Volta Para Casa (2021)",
    ],
    "comedia": [
        "Se Beber, Não Case! (2009)",
        "Ghostbusters (1984)",
        "O Poderoso Chefão (parodia) (2022)",
        "Deadpool (2016)",
        "As Branquelas (2004)",
        "Tropa de Elite (2007)",
    ],
    "scifi": [
        "Matrix (1999)",
        "Interestelar (2014)",
        "Blade Runner 2049 (2017)",
        "Ex Machina (2014)",
        "A Origem (2010)",
        "O Primeiro Contato (2016)",
    ],
    "drama": [
        "Clube da Luta (1999)",
        "O Poderoso Chefão (1972)",
        "Forrest Gump (1994)",
        "A Lista de Schindler (1993)",
        "O Senhor dos Anéis (2001)",
    ],
    "terror": [
        "O Exorcista (1973)",
        "Hereditary (2018)",
        "O Iluminado (1980)",
        "Get Out (2017)",
        "A Bruxa (2015)",
    ],
}

PERGUNTAS_QUIZ = [
    {"pergunta": "Qual é a capital da França?", "resposta": "Paris"},
    {"pergunta": "Quem pintou a Mona Lisa?", "resposta": "Leonardo da Vinci"},
    {"pergunta": "Qual é o maior planeta do sistema solar?", "resposta": "Júpiter"},
    {"pergunta": "Em que ano o Brasil foi descoberto?", "resposta": "1500"},
    {"pergunta": "Qual é o elemento químico mais abundante?", "resposta": "Hidrogênio"},
    {"pergunta": "Quem escreveu 'O Pequeno Príncipe'?", "resposta": "Antoine de Saint-Exupéry"},
    {"pergunta": "Qual é a velocidade da luz?", "resposta": "299.792 km/s"},
    {"pergunta": "Qual é o maior oceano do mundo?", "resposta": "Oceano Pacífico"},
    {"pergunta": "Quem inventou a lâmpada elétrica?", "resposta": "Thomas Edison"},
    {"pergunta": "Qual é a fórmula química da água?", "resposta": "H2O"},
]


class Entretenimento:
    """Módulo de entretenimento."""

    def __init__(self, brain=None):
        self.brain = brain
        self._jogo_ativo = False
        self._numero_secreto = 0
        self._tentativas_jogo = 0
        self._max_tentativas = 7
        self._quiz_atual = None

    # ═══ PIADAS ═══

    def piada(self) -> str:
        """Retorna uma piada aleatória."""
        return random.choice(PIADAS)

    # ═══ CURIOSIDADES ═══

    def curiosidade(self) -> str:
        """Retorna uma curiosidade aleatória."""
        return random.choice(CURIOSIDADES)

    # ═══ JOGO DA ADIVINHAÇÃO ═══

    def iniciar_jogo(self) -> str:
        """Inicia jogo da adivinhação."""
        self._jogo_ativo = True
        self._numero_secreto = random.randint(1, 100)
        self._tentativas_jogo = 0
        self._max_tentativas = 7
        return "Jogo da Adivinhação! Adivinhe um número entre 1 e 100. Você tem 7 tentativas."

    def adivinhar(self, numero: int) -> str:
        """Tenta adivinhar o número."""
        if not self._jogo_ativo:
            return "Nenhum jogo ativo. Diga 'Jarvis jogar adivinha' para começar."

        self._tentativas_jogo += 1

        if numero == self._numero_secreto:
            self._jogo_ativo = False
            return f"Parabéns! Você acertou em {self._tentativas_jogo} tentativas!"
        
        if self._tentativas_jogo >= self._max_tentativas:
            self._jogo_ativo = False
            return f"Game over! O número era {self._numero_secreto}."

        if numero < self._numero_secreto:
            return f"Maior! (Tentativa {self._tentativas_jogo}/{self._max_tentativas})"
        else:
            return f"Menor! (Tentativa {self._tentativas_jogo}/{self._max_tentativas})"

    # ═══ QUIZ ═══

    def proxima_pergunta(self) -> str:
        """Retorna próxima pergunta do quiz."""
        self._quiz_atual = random.choice(PERGUNTAS_QUIZ)
        return f"Quiz: {self._quiz_atual['pergunta']}"

    def verificar_resposta(self, resposta: str) -> str:
        """Verifica resposta do quiz."""
        if not self._quiz_atual:
            return "Nenhuma pergunta ativa. Diga 'Jarvis quiz' para começar."

        resposta_correta = self._quiz_atual["resposta"].lower()
        resposta_user = resposta.lower().strip()

        if resposta_user == resposta_correta or resposta_correta in resposta_user:
            self._quiz_atual = None
            return f"Correto! A resposta é {self._quiz_atual['resposta'] if self._quiz_atual else resposta_correta}."
        
        self._quiz_atual = None
        return f"Incorreto. A resposta era: {self._quiz_atual['resposta'] if self._quiz_atual else resposta_correta}."

    # ═══ RECOMENDAÇÕES ═══

    def recomendar_filme(self, genero: Optional[str] = None) -> str:
        """Recomenda um filme."""
        if genero and genero.lower() in FILMES:
            filme = random.choice(FILMES[genero.lower()])
            return f"Recomendo: {filme}"
        
        # Escolhe gênero aleatório
        genero_aleatorio = random.choice(list(FILMES.keys()))
        filme = random.choice(FILMES[genero_aleatorio])
        return f"Recomendo ({genero_aleatorio}): {filme}"

    def listar_generos(self) -> str:
        """Lista gêneros disponíveis."""
        return f"Gêneros disponíveis: {', '.join(FILMES.keys())}"

    # ═══ FATAL 68 ═══

    def falar_frase_famous(self) -> str:
        """Fala uma frase famosa de tecnologia."""
        frases = [
            "A tecnologia é melhor quando une as pessoas. - Matt Mullenweg",
            "O futuro pertence àqueles que acreditam na beleza de seus sonhos. - Eleanor Roosevelt",
            "Inovar é o que um líder faz de diferente de um gerenciador. - Thomas Watson",
            "O único modo de fazer um bom trabalho é amar o que você faz. - Steve Jobs",
            "A simplicidade é a sofisticação suprema. - Leonardo da Vinci",
            "Nós nos tornamos o que repetidamente fazemos. Excellence, then, is not ato, mas hábito. - Will Durant",
            "O sucesso é ir de fracasso em fracasso sem perder entusiasmo. - Winston Churchill",
            "A imaginação é mais importante que o conhecimento. - Albert Einstein",
        ]
        return random.choice(frases)


# ═══ SINGLETON ═══

_entretenimento_instance = None

def get_entretenimento(brain=None):
    global _entretenimento_instance
    if _entretenimento_instance is None:
        _entretenimento_instance = Entretenimento(brain=brain)
    return _entretenimento_instance
