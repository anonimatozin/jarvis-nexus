"""Intent Classifier v3 - separador robusto."""
import re
import json
import os
from pathlib import Path

from modules.nlu.normalizer import (
    normalizar, normalizar_sem_acento, detectar_contexto_irrelevante
)
from modules.nlu.intents import (
    INTENTS, get_todos_exemplos, get_keywords, get_blockers,
    extrair_parametro
)


_embeddings_cache = None
_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model
    try:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2"
        )
        return _embedding_model
    except Exception as e:
        print(f"[NLU] embeddings indisponivel: {e}")
        return None


def _construir_cache_embeddings():
    global _embeddings_cache
    if _embeddings_cache is not None:
        return _embeddings_cache
    model = _get_embedding_model()
    if not model:
        return None
    exemplos = get_todos_exemplos()
    frases = [normalizar(ex) for _, ex in exemplos]
    try:
        vetores = model.encode(frases, show_progress_bar=False)
        _embeddings_cache = list(zip([n for n, _ in exemplos], vetores))
        print(f"[NLU] Embeddings cache: {len(_embeddings_cache)} exemplos")
        return _embeddings_cache
    except Exception as e:
        print(f"[NLU] erro cache: {e}")
        return None


def _camada_rapida(texto_norm, texto_original):
    candidatos = []
    for nome, dados in INTENTS.items():
        blockers = dados.get("blockers", [])
        if any(b in texto_norm for b in blockers):
            continue
        kws = dados.get("keywords", []) + dados.get("extra_keywords", [])
        matches = 0
        peso_total = 0
        match_inicio = False
        for kw in kws:
            if kw in texto_norm:
                matches += 1
                peso_total += len(kw.split())
                if texto_norm.startswith(kw) or texto_norm.startswith(" " + kw):
                    match_inicio = True
        if matches > 0:
            score = 0.5 + (matches * 0.15) + (peso_total * 0.05)
            if match_inicio:
                score += 0.1
            score = min(score, 0.98)
            candidatos.append((nome, score, matches))
    if not candidatos:
        return None
    candidatos.sort(key=lambda x: (-x[2], -x[1]))
    nome, score, _ = candidatos[0]
    if nome.startswith("clima_") and detectar_contexto_irrelevante(texto_original):
        return None
    return (nome, score)


def _cosine(a, b):
    import numpy as np
    a = np.array(a); b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def _camada_semantica(texto_norm):
    cache = _construir_cache_embeddings()
    if not cache:
        return None
    model = _get_embedding_model()
    if not model:
        return None
    try:
        vet = model.encode([texto_norm], show_progress_bar=False)[0]
    except Exception:
        return None
    scores = []
    for intent_name, exemplo_vec in cache:
        sim = _cosine(vet, exemplo_vec)
        scores.append((intent_name, sim))
    if not scores:
        return None
    por_intent = {}
    for intent, sim in scores:
        if intent not in por_intent or sim > por_intent[intent]:
            por_intent[intent] = sim
    filtrado = {}
    for intent, sim in por_intent.items():
        blockers = INTENTS.get(intent, {}).get("blockers", [])
        if any(b in texto_norm for b in blockers):
            continue
        filtrado[intent] = sim
    if not filtrado:
        return None
    ranking = sorted(filtrado.items(), key=lambda x: -x[1])
    return (ranking[0][0], ranking[0][1])


def _camada_ia(texto_original, brain):
    if not brain:
        return None
    intents_lista = list(INTENTS.keys())
    intents_str = ", ".join(intents_lista)

    # SISTEMA SEPARADO: nao usa historico de conversa
    # Usa think_raw se disponivel, senao think com flag
    prompt = (
        "Voce e um classificador. Responda APENAS o nome da categoria, nada mais.\n"
        f"CATEGORIAS VALIDAS: {intents_str}\n"
        "REGRAS ABSOLUTAS:\n"
        "- Responda SO o nome da categoria (ex: hora_atual)\n"
        "- Se nao encaixar em nenhuma: responda outros\n"
        "- NUNCA responda a pergunta, NUNCA explique\n"
        "- UMA palavra apenas\n"
        f"FRASE PARA CLASSIFICAR: {texto_original}\n"
        "CATEGORIA:"
    )
    try:
        # Tenta usar think sem historico (evita contaminacao)
        if hasattr(brain, "think_sem_historico"):
            resposta = brain.think_sem_historico(prompt)
        else:
            resposta = brain.think(prompt, usar_historico=False)
        if not resposta:
            return None
        # Pega so a primeira palavra, remove tudo que nao for letra/underscore
        primeira = resposta.strip().lower().split()[0] if resposta.strip() else ""
        primeira = re.sub(r"[^a-z_]", "", primeira)
        if primeira in INTENTS:
            return (primeira, 0.85)
        # Qualquer resposta fora dos intents = fallback (nao chama brain de novo)
        return None
    except Exception as e:
        print(f"[NLU IA] {e}")
        return None


# ════════════════════════════════════════════════════════════
# MULTI-COMANDO v3 - separa de verdade sem confundir
# ════════════════════════════════════════════════════════════

def separar_multi_comando(texto):
    """
    Separa frases conectadas SEM quebrar padroes importantes.
    Exemplos protegidos:
      "em 5 minutos de tomar agua" - nao quebra "de tomar agua"
      "lembre disso meu nome e Joao" - nao quebra "e Joao"
    """
    if not texto:
        return []

    # Protege padroes que NAO podem ser separados
    PROTECTED = []

    # 1. "em X (segundos|minutos|horas) de Y"
    # Captura ate o proximo conector explicito (vou separar so apos isso)
    pattern_lembrete = re.compile(
        r"(em|daqui)\s+\d+\s+(segundo|minuto|hora)s?\s+(de|para|que)\s+[^,]+?(?=\s+e\s+abr|\s+e\s+toc|\s+e\s+pausa|\s+e\s+ativ|$|,)",
        re.IGNORECASE
    )

    txt_safe = texto
    for i, m in enumerate(pattern_lembrete.finditer(texto)):
        marker = f"__PROT{i}__"
        PROTECTED.append((marker, m.group(0)))
        txt_safe = txt_safe.replace(m.group(0), marker)

    # 2. "lembre disso ... e ..." - protege ate o final
    pattern_memoria = re.compile(
        r"(lembre disso|guarde isso|anote isso|memoriza isso|salva isso)[:\s]+.+",
        re.IGNORECASE
    )
    for i, m in enumerate(pattern_memoria.finditer(txt_safe)):
        marker = f"__PROTM{i}__"
        PROTECTED.append((marker, m.group(0)))
        txt_safe = txt_safe.replace(m.group(0), marker)

    # Conectores na ordem certa (mais especificos primeiro)
    CONECTORES = [
        " e tambem ", ", tambem ", " tambem ",
        " e depois ", " depois ",
        " e ai ",
        " entao ",
        "; ",
    ]
    partes = [txt_safe]
    for conector in CONECTORES:
        novas = []
        for p in partes:
            novas.extend(p.split(conector))
        partes = novas

    # " e " com palavra completa
    novas = []
    for p in partes:
        sub = re.split(r"\s+e\s+", p)
        novas.extend(sub)
    partes = novas

    # Restaura
    partes_final = []
    for p in partes:
        for marker, original in PROTECTED:
            p = p.replace(marker, original)
        p = p.strip(" ,.;")
        if len(p) >= 3:
            partes_final.append(p)

    return partes_final if partes_final else [texto]


CONFIANCA_MIN_RAPIDA = 0.75
CONFIANCA_MIN_SEMANTICA = 0.65



# Intents que nao devem ser classificados (deixa Brain decidir)
DEV_BLOQUEADOS = {
    "dev_listar_pasta", "dev_ler_arquivo", "dev_mover_arquivo",
    "dev_organizar_downloads", "dev_espaco_disco", "dev_criar_modulo",
    "dev_tarefa_agente", "dev_analisar_codigo", "dev_drives",
}

def classificar(texto, brain=None):
    if not texto:
        return None
    texto_norm = normalizar(texto)
    texto_norm_sa = normalizar_sem_acento(texto)
    r1 = _camada_rapida(texto_norm_sa, texto)
    if r1 and r1[1] >= CONFIANCA_MIN_RAPIDA:
        return {
            "intent": r1[0], "confidence": r1[1],
            "parametros": extrair_parametro(r1[0], texto),
            "camada": "rapida", "texto_norm": texto_norm,
        }
    r2 = _camada_semantica(texto_norm)
    if r2 and r2[1] >= CONFIANCA_MIN_SEMANTICA:
        return {
            "intent": r2[0], "confidence": r2[1],
            "parametros": extrair_parametro(r2[0], texto),
            "camada": "semantica", "texto_norm": texto_norm,
        }
    r3 = _camada_ia(texto, brain)
    if r3:
        return {
            "intent": r3[0], "confidence": r3[1],
            "parametros": extrair_parametro(r3[0], texto),
            "camada": "ia", "texto_norm": texto_norm,
        }
    return {
        "intent": "fallback_ia", "confidence": 0.3,
        "parametros": None, "camada": "fallback",
        "texto_norm": texto_norm,
    }


def classificar_multi(texto, brain=None):
    partes = separar_multi_comando(texto)
    resultados = []
    for p in partes:
        r = classificar(p, brain=brain)
        if r:
            r["texto_original"] = p
            resultados.append(r)
    return resultados


LEARN_FILE = Path("data/nlu_learned.json")


def aprender_intent(texto, intent_correto):
    try:
        LEARN_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if LEARN_FILE.exists():
            data = json.loads(LEARN_FILE.read_text(encoding="utf-8"))
        data.setdefault(intent_correto, []).append(texto)
        LEARN_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                              encoding="utf-8")
        if intent_correto in INTENTS:
            INTENTS[intent_correto].setdefault("exemplos", []).append(texto)
            global _embeddings_cache
            _embeddings_cache = None
        return True
    except Exception as e:
        print(f"[NLU APRENDIZ] {e}")
        return False


def carregar_aprendizados():
    try:
        if not LEARN_FILE.exists():
            return 0
        data = json.loads(LEARN_FILE.read_text(encoding="utf-8"))
        total = 0
        for intent, frases in data.items():
            if intent in INTENTS:
                INTENTS[intent].setdefault("exemplos", []).extend(frases)
                total += len(frases)
        return total
    except Exception as e:
        print(f"[NLU LOAD] {e}")
        return 0
