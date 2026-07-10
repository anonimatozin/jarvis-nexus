"""
Normaliza texto: remove gírias, sotaques regionais, pontuacao.
"""
import re
import unicodedata

# Converte palavras em numeros (pt-BR)
PALAVRAS_NUMEROS = {
    "um": "1", "uma": "1", "dois": "2", "duas": "2",
    "tres": "3", "três": "3", "quatro": "4", "cinco": "5",
    "seis": "6", "sete": "7", "oito": "8", "nove": "9",
    "dez": "10", "onze": "11", "doze": "12", "treze": "13",
    "quatorze": "14", "catorze": "14", "quinze": "15",
    "dezesseis": "16", "dezessete": "17", "dezoito": "18",
    "dezenove": "19", "vinte": "20",
}

def converter_palavras_numeros(texto):
    """'cinco' -> '5', 'dez soldados' -> '10 soldados'."""
    if not texto:
        return texto
    palavras = texto.split()
    novas = []
    for p in palavras:
        p_clean = p.lower().strip(".,!?;:")
        if p_clean in PALAVRAS_NUMEROS:
            novas.append(PALAVRAS_NUMEROS[p_clean])
        else:
            novas.append(p)
    return " ".join(novas)




# Mapa de sinonimos/girias -> palavra base
SINONIMOS = {
    # Gírias regionais
    "mn": "", "mano": "", "brother": "", "bro": "", "véi": "",
    "véio": "", "tchê": "", "tche": "", "uai": "", "ué": "",
    "consagrado": "", "meu filho": "", "meu rei": "", "meu chapa": "",
    "parceiro": "", "irmão": "", "irmao": "", "ô": "", "e aí": "",
    "e ai": "", "bah": "", "pô": "", "po": "", "cara": "",
    "fera": "", "chefia": "",

    # Variações de chuva
    "molhar": "chover", "molhar a gente": "chover",
    "agua do céu": "chover", "agua do ceu": "chover",
    "chuvinha": "chuva", "chuvarada": "chuva", "pancada": "chuva",
    "temporal": "chuva",

    # Variações de clima
    "tempo": "clima", "temperatura": "clima",

    # Variações de hora
    "horario": "hora", "horas": "hora", "que horas": "hora",
    "ke horas": "hora",

    # Variações de abrir
    "iniciar": "abrir", "executar": "abrir", "rodar": "abrir",
    "subir": "abrir", "lança": "abrir", "lancar": "abrir",

    # Variações de fechar
    "encerrar": "fechar", "matar": "fechar", "kill": "fechar",
    "derruba": "fechar", "mata": "fechar",

    # Pendrive
    "pen drive": "pendrive", "pen-drive": "pendrive",

    # PC
    "computador": "pc", "máquina": "pc", "maquina": "pc",
}


# Palavras que indicam pergunta
INDICADORES_PERGUNTA = [
    "será que", "sera que", "tipo", "acha que", "ce acha",
    "voce acha", "vc acha", "sera", "porventura",
    "por acaso", "qual a chance",
]


def remover_acentos(texto):
    """Remove acentos pra facilitar match."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar(texto):
    # Converte palavras em numeros primeiro
    if texto:
        texto = converter_palavras_numeros(texto)
    """
    Pipeline completo:
    1. Lowercase
    2. Remove pontuacao desnecessaria
    3. Substitui sinonimos
    4. Remove indicadores de pergunta (deixa o resto)
    5. Remove espacos duplos
    """
    if not texto:
        return ""

    t = texto.lower().strip()

    # Remove pontuacao final
    t = re.sub(r"[?!.,;]+$", "", t)

    # Substitui sinonimos (palavra inteira)
    for original, substituto in SINONIMOS.items():
        # palavra completa, com espaco antes e depois (ou inicio/fim)
        pattern = r"(?:^|\s)" + re.escape(original) + r"(?=\s|$)"
        if substituto:
            t = re.sub(pattern, " " + substituto, t)
        else:
            t = re.sub(pattern, " ", t)

    # Remove indicadores de pergunta (mantém o conteúdo)
    for ind in INDICADORES_PERGUNTA:
        t = t.replace(ind, "")

    # Limpa espaços duplos
    t = re.sub(r"\s+", " ", t).strip()

    return t


def normalizar_sem_acento(texto):
    return remover_acentos(normalizar(texto))


def detectar_contexto_irrelevante(texto_original):
    """
    Detecta se uma palavra-gatilho aparece em contexto irrelevante.
    Ex: "fiz pão, será que vai molhar" - molhar = pão, não clima.

    Retorna True se for contexto irrelevante (= ignora handler especifico).
    """
    tl = texto_original.lower()

    # Padroes que indicam contexto NAO meteorologico
    contextos_nao_clima = [
        ("molhar", ["roupa", "pão", "pao", "bolo", "massa", "tinta",
                    "cabelo", "carro", "sapato", "panela", "comida"]),
        ("chover", ["dinheiro", "presente", "ideia", "trabalho"]),
        ("status", ["instagram", "facebook", "whatsapp", "rede social",
                    "feed", "story"]),
    ]

    for palavra_chave, contextos in contextos_nao_clima:
        if palavra_chave in tl:
            for ctx in contextos:
                if ctx in tl:
                    return True
    return False
