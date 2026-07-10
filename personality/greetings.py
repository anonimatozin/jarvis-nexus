# personality/greetings.py
"""
J.A.R.V.I.S. - Sistema de Saudações Contextuais
Saudações que mudam baseadas na hora do dia, dia da semana,
e número de interações com o usuário.
"""

import random
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import USER_NAME, JARVIS_NAME, VERSION, CODENAME


def get_time_period() -> str:
    """Retorna o período do dia atual."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"


def get_greeting() -> str:
    """
    Retorna uma saudação contextual baseada na hora do dia.
    Varia aleatoriamente para não ser repetitivo.
    """
    period = get_time_period()
    
    greetings = {
        "morning": [
            f"Bom dia, {USER_NAME}. Todos os sistemas estão operacionais.",
            f"Bom dia, {USER_NAME}. Espero que tenha descansado bem. Estou pronto para começar.",
            f"Bom dia. Café e código — uma combinação perfeita, {USER_NAME}.",
        ],
        "afternoon": [
            f"Boa tarde, {USER_NAME}. Como posso ser útil?",
            f"Boa tarde. Sistemas funcionando perfeitamente, {USER_NAME}.",
            f"Boa tarde, {USER_NAME}. Estou à disposição.",
        ],
        "evening": [
            f"Boa noite, {USER_NAME}. Ainda produtivo, eu vejo.",
            f"Boa noite. Todos os módulos online e aguardando instruções, {USER_NAME}.",
            f"Boa noite, {USER_NAME}. Em que posso ajudar?",
        ],
        "night": [
            f"Trabalhando até tarde, {USER_NAME}? Estou aqui se precisar.",
            f"Boa madrugada, {USER_NAME}. Os melhores projetos nascem nessa hora.",
            f"Ainda acordado, {USER_NAME}? Vamos ser produtivos então.",
        ]
    }
    
    return random.choice(greetings[period])


def get_startup_message() -> str:
    """Mensagem completa de inicialização do sistema."""
    greeting = get_greeting()
    return (
        f"{greeting} "
        f"{JARVIS_NAME} versão {VERSION}, codinome {CODENAME}, totalmente operacional."
    )


def get_shutdown_message() -> str:
    """Mensagem de desligamento."""
    messages = [
        f"Encerrando todos os sistemas. Até logo, {USER_NAME}.",
        f"Entrando em modo de espera. Foi um prazer, {USER_NAME}.",
        f"Sistemas sendo desligados com segurança. Boa noite, {USER_NAME}.",
        f"Desligando. Estarei aqui quando precisar, {USER_NAME}.",
    ]
    return random.choice(messages)


def get_error_response() -> str:
    """Resposta elegante para erros."""
    messages = [
        f"Houve uma pequena turbulência nos meus circuitos, {USER_NAME}. Posso tentar novamente.",
        "Encontrei um obstáculo inesperado. Permitir que eu recalibre e tente outra abordagem?",
        f"Isso não saiu como planejado, {USER_NAME}. Vou analisar e corrigir.",
    ]
    return random.choice(messages)


def get_acknowledgment() -> str:
    """Confirmações rápidas e variadas."""
    messages = [
        "Entendido.",
        "Compreendido, Sir.",
        "Prontamente.",
        "Imediatamente.",
        "Considerado e processado.",
        "Às suas ordens.",
        "Já estou nisto.",
    ]
    return random.choice(messages)