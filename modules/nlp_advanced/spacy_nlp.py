"""
JARVIS NLP Advanced v1.0
Processamento de linguagem natural avançado com spaCy.

Baseado em: explosion/spaCy (33.7k stars)
Recursos:
  - Named Entity Recognition (NER)
  - Análise de sentimento
  - Extração de informações
  - Classificação de texto
  - Similaridade semântica
  - Multi-idioma (70+)
"""
import os
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# ═══ DEPENDENCIAS ═══
_spacy_ok = False
_nlp_models = {}

try:
    import spacy
    _spacy_ok = True
except ImportError:
    pass


class NLPAdvanced:
    """NLP avançado com spaCy."""

    # Mapeamento de idiomas para modelos
    MODELOS = {
        "pt": "pt_core_news_sm",
        "en": "en_core_web_sm",
        "es": "es_core_news_sm",
        "fr": "fr_core_news_sm",
        "de": "de_core_news_sm",
        "it": "it_core_news_sm",
        "ja": "ja_core_news_sm",
        "zh": "zh_core_web_sm",
    }

    def __init__(self, idioma: str = "pt"):
        self.idioma = idioma
        self._nlp = None

        if not _spacy_ok:
            print("[NLP] spaCy não instalado")
            print("  Instale com: pip install spacy")
            return

        self._carregar_modelo(idioma)

    def _carregar_modelo(self, idioma: str):
        """Carrega modelo spaCy para o idioma."""
        global _nlp_models

        if idioma in _nlp_models:
            self._nlp = _nlp_models[idioma]
            print(f"[NLP] Modelo {idioma} carregado (cache)")
            return

        modelo = self.MODELOS.get(idioma, f"{idioma}_core_news_sm")

        try:
            self._nlp = spacy.load(modelo)
            _nlp_models[idioma] = self._nlp
            print(f"[NLP] Modelo carregado: {modelo}")
        except OSError:
            print(f"[NLP] Modelo {modelo} não encontrado")
            print(f"  Instale com: python -m spacy download {modelo}")
            # Tenta carregar modelo padrão
            try:
                self._nlp = spacy.load("en_core_web_sm")
                _nlp_models[idioma] = self._nlp
                print(f"[NLP] Usando modelo padrão: en_core_web_sm")
            except OSError:
                print("[NLP] Nenhum modelo disponível")

    def processar(self, texto: str) -> Optional[Any]:
        """Processa texto com spaCy."""
        if not self._nlp:
            return None
        return self._nlp(texto)

    def extrair_entidades(self, texto: str) -> List[Dict]:
        """Extrai entidades nomeadas (NER)."""
        doc = self.processar(texto)
        if not doc:
            return []

        entidades = []
        for ent in doc.ents:
            entidades.append({
                "texto": ent.text,
                "tipo": ent.label_,
                "inicio": ent.start_char,
                "fim": ent.end_char,
                "explicacao": spacy.explain(ent.label_) or ent.label_
            })
        return entidades

    def analisar_sentimento(self, texto: str) -> Dict:
        """Análise de sentimento baseada em regras."""
        doc = self.processar(texto)
        if not doc:
            return {"sentimento": "neutro", "confianca": 0}

        # Palavras positivas e negativas comuns
        positivos = {
            "bom", "ótimo", "excelente", "maravilhoso", "perfeito",
            "feliz", "alegre", "satisfeito", "adorei", "amei",
            "good", "great", "excellent", "wonderful", "perfect",
            "happy", "love", "amazing", "fantastic", "brilliant"
        }
        negativos = {
            "ruim", "péssimo", "terrível", "horrível", "odioso",
            "triste", "raiva", "decepcionado", "odeio", "detesto",
            "bad", "terrible", "horrible", "awful", "hate",
            "sad", "angry", "disappointed", "worst", "poor"
        }

        texto_lower = texto.lower()
        palavras = set(re.findall(r'\b\w+\b', texto_lower))

        pos_count = len(palavras & positivos)
        neg_count = len(palavras & negativos)

        total = pos_count + neg_count
        if total == 0:
            return {"sentimento": "neutro", "confianca": 0.5}

        score = (pos_count - neg_count) / total
        if score > 0.2:
            sentimento = "positivo"
        elif score < -0.2:
            sentimento = "negativo"
        else:
            sentimento = "neutro"

        return {
            "sentimento": sentimento,
            "confianca": round(abs(score), 2),
            "positivo": pos_count,
            "negativo": neg_count
        }

    def extrair_palavras_chave(self, texto: str, top_n: int = 10) -> List[str]:
        """Extrai palavras-chave do texto."""
        doc = self.processar(texto)
        if not doc:
            return []

        # Filtra stopwords e pontuação
        palavras = []
        for token in doc:
            if (not token.is_stop and not token.is_punct and
                not token.is_space and len(token.text) > 2):
                palavras.append(token.lemma_.lower())

        # Conta frequência
        from collections import Counter
        frequencia = Counter(palavras)

        return [word for word, _ in frequencia.most_common(top_n)]

    def calcular_similaridade(self, texto1: str, texto2: str) -> float:
        """Calcula similaridade entre dois textos."""
        doc1 = self.processar(texto1)
        doc2 = self.processar(texto2)

        if doc1 and doc2:
            return doc1.similarity(doc2)
        return 0.0

    def resumir_texto(self, texto: str, num_frases: int = 3) -> str:
        """Resumo extrativo do texto."""
        doc = self.processar(texto)
        if not doc:
            return texto[:200]

        # Calcula importância das frases
        frases = list(doc.sents)
        if len(frases) <= num_frases:
            return " ".join([f.text for f in frases])

        # Pontua frases por posição e entidades
        pontuacoes = []
        for i, frase in enumerate(frases):
            score = 0
            # Primeiras frases são mais importantes
            if i < 3:
                score += 3 - i
            # Frases com entidades são mais importantes
            for ent in frase.ents:
                score += 1
            # Frases mais longas tendem a ser mais informativas
            score += len(frase.text.split()) / 10
            pontuacoes.append((i, score))

        # Ordena por pontuação e pega as melhores
        pontuacoes.sort(key=lambda x: x[1], reverse=True)
        melhores = sorted([p[0] for p in pontuacoes[:num_frases]])

        return " ".join([frases[i].text for i in melhores])

    def classificar_texto(self, texto: str, categorias: List[str]) -> Optional[str]:
        """Classifica texto em categorias pré-definidas."""
        texto_lower = texto.lower()
        melhor_cat = None
        melhor_score = 0

        for cat in categorias:
            palavras_cat = set(cat.lower().split())
            palavras_texto = set(re.findall(r'\b\w+\b', texto_lower))
            intersecao = len(palavras_cat & palavras_texto)
            if intersecao > melhor_score:
                melhor_score = intersecao
                melhor_cat = cat

        return melhor_cat

    def traduzir_entidade(self, entidade: str) -> str:
        """Traduz nome de entidade para português."""
        traducoes = {
            "PERSON": "Pessoa",
            "ORG": "Organização",
            "GPE": "Local",
            "LOC": "Localização",
            "DATE": "Data",
            "TIME": "Hora",
            "MONEY": "Dinheiro",
            "PERCENT": "Porcentagem",
            "PRODUCT": "Produto",
            "EVENT": "Evento",
            "WORK_OF_ART": "Obra de Arte",
            "LAW": "Lei",
            "LANGUAGE": "Idioma",
            "NORP": "Nacionalidade/Religião",
            "FAC": "Facilidade",
            "CARDINAL": "Cardinal",
            "ORDINAL": "Ordinal",
            "QUANTITY": "Quantidade",
        }
        return traducoes.get(entidade, entidade)

    def status(self) -> Dict:
        """Retorna status do NLP."""
        return {
            "spacy_ok": _spacy_ok,
            "idioma": self.idioma,
            "modelo_carregado": self._nlp is not None,
            "modelos_disponiveis": list(self.MODELOS.keys())
        }


# ═══ INSTANCIA GLOBAL ═══
_nlp_instance = None


def get_nlp_advanced(idioma: str = "pt") -> NLPAdvanced:
    """Retorna instância do NLP Advanced."""
    global _nlp_instance
    if _nlp_instance is None:
        _nlp_instance = NLPAdvanced(idioma)
    return _nlp_instance
