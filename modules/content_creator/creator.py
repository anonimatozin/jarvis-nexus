"""
JARVIS Content Creator v1.0
Criação e edição de conteúdo assistida por IA.

Baseado em: AJaySi/AI-Writer (529 stars)
Recursos:
  - Geração de posts para redes sociais
  - Criação de artigos
  - SEO otimizado
  - Templates prontos
  - Análise de conteúdo
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading


class ContentCreator:
    """Criador de conteúdo inteligente."""

    # Templates de conteúdo
    TEMPLATES = {
        "post_linkedin": {
            "nome": "Post LinkedIn",
            "estrutura": [
                "Hook (primeira linha impactante)",
                "Problema/Dor do público",
                "Solução/Insight",
                "Exemplo prático",
                "Call to action"
            ],
            "tamanho_max": 3000
        },
        "post_twitter": {
            "nome": "Tweet/Thread",
            "estrutura": [
                "Mensagem principal (280 chars)",
                "Thread com detalhes (se necessário)",
                "Hashtags relevantes"
            ],
            "tamanho_max": 280
        },
        "artigo_blog": {
            "nome": "Artigo de Blog",
            "estrutura": [
                "Título otimizado SEO",
                "Introdução atrativa",
                "H2 com tópicos principais",
                "Listas e exemplos",
                "Conclusão com CTA"
            ],
            "tamanho_max": 5000
        },
        "email_marketing": {
            "nome": "Email Marketing",
            "estrutura": [
                "Assunto curioso",
                "Saudação personalizada",
                "Corpo com valor",
                "Oferta/Proposta",
                "CTA claro"
            ],
            "tamanho_max": 2000
        },
        "descricao_produto": {
            "nome": "Descrição de Produto",
            "estrutura": [
                "Título do produto",
                "Benefícios principais",
                "Características",
                "Prova social",
                "Garantia/Oferta"
            ],
            "tamanho_max": 1500
        }
    }

    # Hashtags por nicho
    HASHTAGS = {
        "tecnologia": ["#tech", "#inovacao", "#digital", "#futuro", "#ia"],
        "marketing": ["#marketing", "#digital", "#vendas", "#negocios", "#empreendedorismo"],
        "saude": ["#saude", "#bemestar", "#vida", "#fitness", "#nutricao"],
        "educacao": ["#educacao", "#aprendizado", "#cursos", "#conhecimento"],
        "financas": ["#financas", "#investimentos", "#economia", "#dinheiro"]
    }

    def __init__(self):
        self._historico = []
        self._lock = threading.Lock()

        print("[CONTENT] Criador de conteúdo inicializado")
        print(f"  Templates: {len(self.TEMPLATES)}")

    def gerar_post(self, tema: str, plataforma: str = "linkedin",
                   tom: str = "profissional", nicho: str = None) -> Dict:
        """Gera post para rede social."""
        template = self.TEMPLATES.get(f"post_{plataforma}", self.TEMPLATES["post_linkedin"])

        # Gera conteúdo baseado no template
        conteudo = {
            "plataforma": plataforma,
            "tema": tema,
            "tom": tom,
            "template": template["nome"],
            "tamanho_max": template["tamanho_max"],
            "estrutura": template["estrutura"],
            "hashtags": self._obter_hashtags(nicho),
            "sugestoes": self._gerar_sugestoes(tema, plataforma)
        }

        # Gera rascunho
        conteudo["rascunho"] = self._gerar_rascunho(tema, plataforma, tom)

        self._salvar_historico(conteudo)
        return conteudo

    def _obter_hashtags(self, nicho: str = None) -> List[str]:
        """Retorna hashtags relevantes."""
        if nicho and nicho in self.HASHTAGS:
            return self.HASHTAGS[nicho][:5]
        # Retorna hashtags genéricas
        return ["#conteudo", "#qualidade", "#relevancia"]

    def _gerar_sugestoes(self, tema: str, plataforma: str) -> List[str]:
        """Gera sugestões de conteúdo."""
        sugestoes = []

        if plataforma == "linkedin":
            sugestoes.extend([
                f"Compartilhe uma experiência pessoal sobre {tema}",
                f"Liste 5 dicas práticas sobre {tema}",
                f"Conte um caso de sucesso relacionado a {tema}",
                f"Faça uma pergunta provocativa sobre {tema}"
            ])
        elif plataforma == "twitter":
            sugestoes.extend([
                f"Tweet principal: definição de {tema}",
                f"Thread: 7 fatos sobre {tema}",
                f"Poll: O que você acha sobre {tema}?",
                f"Curiosidade sobre {tema}"
            ])
        else:
            sugestoes.extend([
                f"Introdução sobre {tema}",
                f"Lista de benefícios de {tema}",
                f"Como aplicar {tema} na prática"
            ])

        return sugestoes

    def _gerar_rascunho(self, tema: str, plataforma: str, tom: str) -> str:
        """Gera rascunho do conteúdo."""
        if plataforma == "linkedin":
            return f"""🚀 {tema.upper()}

Você sabia que {tema} está transformando o mercado?

Aqui vão 3 pontos importantes:

✅ Primeiro ponto sobre {tema}
✅ Segundo aspecto relevante
✅ Terceiro insight prático

E você, como está aplicando {tema} no seu dia adia?

#conteudo #qualidade #{tema.replace(" ", "")}"""

        elif plataforma == "twitter":
            return f"🧵 THREAD: 5 coisas que você precisa saber sobre {tema}\n\n1/ Primeiro ponto importante\n\n2/ Segundo aspecto relevante\n\n3/ Insight prático"

        else:
            return f"📝 {tema}\n\nIntrodução sobre o tema...\n\nDesenvolvimento com pontos principais...\n\nConclusão com call to action."

    def otimizar_seo(self, titulo: str, conteudo: str) -> Dict:
        """Otimiza conteúdo para SEO."""
        palavras = conteudo.lower().split()
        total_palavras = len(palavras)

        # Conta palavras-chave
        palavras_chave = {}
        for palavra in palavras:
            if len(palavra) > 4:
                palavras_chave[palavra] = palavras_chave.get(palavra, 0) + 1

        # Top palavras
        top_palavras = sorted(palavras_chave.items(), key=lambda x: x[1], reverse=True)[:10]

        # Análise SEO
        analise = {
            "titulo": titulo,
            "tamanho_titulo": len(titulo),
            "total_palavras": total_palavras,
            "palavras_chave_top": top_palavras,
            "pontuacao_seo": self._calcular_pontuacao_seo(titulo, conteudo),
            "sugestoes": self._sugestoes_seo(titulo, conteudo)
        }

        return analise

    def _calcular_pontuacao_seo(self, titulo: str, conteudo: str) -> int:
        """Calcula pontuação SEO (0-100)."""
        score = 0

        # Título
        if 30 <= len(titulo) <= 60:
            score += 20
        elif 20 <= len(titulo) <= 70:
            score += 10

        # Conteúdo
        palavras = len(conteudo.split())
        if 300 <= palavras <= 2000:
            score += 20
        elif 150 <= palavras <= 3000:
            score += 10

        # Estrutura
        if "\n" in conteudo:
            score += 10  # Tem parágrafos
        if any(emoji in conteudo for emoji in ["✅", " bullet", "1."]):
            score += 10  # Tem listas

        # Palavras-chave
        palavras_chave = len(set(conteudo.lower().split()))
        if palavras_chave > 50:
            score += 20
        elif palavras_chave > 20:
            score += 10

        # Tamanho
        if len(conteudo) > 500:
            score += 20

        return min(100, score)

    def _sugestoes_seo(self, titulo: str, conteudo: str) -> List[str]:
        """Gera sugestões de otimização SEO."""
        sugestoes = []

        if len(titulo) < 30:
            sugestoes.append("Título muito curto. Adicione palavras-chave.")
        if len(titulo) > 60:
            sugestoes.append("Título muito longo. Resuma para melhor CTR.")

        palavras = len(conteudo.split())
        if palavras < 300:
            sugestoes.append("Conteúdo curto. Artigos maiores ranqueiam melhor.")
        if palavras > 2000:
            sugestoes.append("Conteúdo longo. Considere dividir em partes.")

        if "\n" not in conteudo:
            sugestoes.append("Adicione parágrafos para melhor legibilidade.")

        if not any(emoji in conteudo for emoji in ["✅", " bullet", "1."]):
            sugestoes.append("Adicione listas para melhorar o engajamento.")

        return sugestoes

    def gerar_variacoes(self, conteudo: str, num_variacoes: int = 3) -> List[str]:
        """Gera variações do conteúdo."""
        variacoes = []

        # Variação 1: Mais formal
        variacoes.append(conteudo.replace("🚀", "").replace("✅", "•"))

        # Variação 2: Mais casual
        variacoes.append(f"Hey! {conteudo.lower()}")

        # Variação 3: Com emojis diferentes
        variacoes.append(conteudo.replace("🚀", "💡").replace("✅", "👉"))

        return variacoes[:num_variacoes]

    def analisar_engajamento(self, conteudo: str) -> Dict:
        """Analisa potencial de engajamento."""
        # Fatores de engajamento
        fatores = {
            "tem_emoji": bool(re.search(r'[^\w\s,.]', conteudo)),
            "tem_lista": bool(re.search(r'\d\.|✅| bullet', conteudo)),
            "tem_pergunta": "?" in conteudo,
            "tem_hashtag": "#" in conteudo,
            "tem_call_to_action": any(p in conteudo.lower() for p in ["compartilhe", "comente", "curta", "siga"]),
            "tamanho_ideal": 100 <= len(conteudo) <= 500,
            "tem_numero": bool(re.search(r'\d+', conteudo)),
        }

        # Calcula pontuação
        pontuacao = sum(fatores.values()) / len(fatores) * 100

        return {
            "pontuacao": round(pontuacao),
            "fatores": fatores,
            "sugestoes": self._sugestoes_engajamento(fatores)
        }

    def _sugestoes_engajamento(self, fatores: Dict) -> List[str]:
        """Gera sugestões para melhorar engajamento."""
        sugestoes = []

        if not fatores["tem_emoji"]:
            sugestoes.append("Adicione emojis para chamar atenção.")
        if not fatores["tem_lista"]:
            sugestoes.append("Use listas para facilitar a leitura.")
        if not fatores["tem_pergunta"]:
            sugestoes.append("Faça uma pergunta para incentivar comentários.")
        if not fatores["tem_hashtag"]:
            sugestoes.append("Adicione hashtags relevantes.")
        if not fatores["tem_call_to_action"]:
            sugestoes.append("Inclua um call to action claro.")

        return sugestoes

    def _salvar_historico(self, conteudo: Dict):
        """Salva no histórico."""
        with self._lock:
            conteudo["timestamp"] = datetime.now().isoformat()
            self._historico.append(conteudo)
            if len(self._historico) > 100:
                self._historico.pop(0)

    def obter_historico(self) -> List[Dict]:
        """Retorna histórico de conteúdo criado."""
        with self._lock:
            return self._historico.copy()

    def status(self) -> Dict:
        """Retorna status do criador."""
        return {
            "templates": list(self.TEMPLATES.keys()),
            "historico": len(self._historico),
            "nichos": list(self.HASHTAGS.keys())
        }


# ═══ INSTANCIA GLOBAL ═══
_content_instance = None


def get_content_creator() -> ContentCreator:
    """Retorna instância do Content Creator."""
    global _content_instance
    if _content_instance is None:
        _content_instance = ContentCreator()
    return _content_instance
