# personality/persona.py
"""
J.A.R.V.I.S. - Motor de Personalidade Adaptativa v1.0

O Jarvis aprende o estilo do usuário ao longo do tempo e adapta:
  - Tom de voz (formal → informal → estilo próprio do usuário)
  - Nível de humor e sarcasmo
  - Densidade das respostas (verboso → direto)
  - Vocabulário e gírias detectadas
  - Frequência de feedback solicitado

Fases de evolução:
  FASE 1 (0-20 msgs)    : Observador — formal, educado, aprende
  FASE 2 (21-100 msgs)  : Adaptando — começa a espelhar o estilo
  FASE 3 (101-500 msgs) : Calibrado — estilo próprio estabelecido
  FASE 4 (500+ msgs)    : Integrado — extensão natural do usuário
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.database import JarvisMemory
from utils.logger import setup_logger

logger = setup_logger("persona")


# ── Perfil padrão inicial ──────────────────────────────────────────────────
DEFAULT_PROFILE = {
    "humor_level":        "moderado",
    "sarcasm_level":      "baixo",
    "formality_level":    "semi-formal",
    "response_density":   "moderada",
    "feedback_frequency": "baixa",
    "preferred_tone":     "elegante",
    "evolution_phase":    "1",
    "total_interactions": "0",
    "user_style_notes":   "",
}


class PersonaEngine:
    """
    Motor de personalidade adaptativa do Jarvis.

    Lê o perfil atual da memória e constrói o system prompt
    dinâmico que define o comportamento da IA.
    """

    def __init__(self, memory: JarvisMemory):
        self.memory = memory
        self._ensure_default_profile()

    def _ensure_default_profile(self):
        """Garante que o perfil padrão existe no banco."""
        for key, value in DEFAULT_PROFILE.items():
            existing = self.memory.get_personality_trait(key)
            if existing is None:
                self.memory.set_personality_trait(key, value)

    # ──────────────────────────────────────────────────────────────────────
    #  LEITURA DO PERFIL
    # ──────────────────────────────────────────────────────────────────────

    def get_profile(self) -> dict:
        """Retorna o perfil de personalidade atual como dicionário simples."""
        raw = self.memory.get_full_personality_profile()
        return {k: v["value"] for k, v in raw.items()}

    def get_evolution_phase(self) -> int:
        """Retorna a fase de evolução atual (1 a 4)."""
        try:
            return int(self.memory.get_personality_trait("evolution_phase") or "1")
        except ValueError:
            return 1

    def get_interaction_count(self) -> int:
        """Retorna total de interações registradas."""
        try:
            return int(
                self.memory.get_personality_trait("total_interactions") or "0"
            )
        except ValueError:
            return 0

    # ──────────────────────────────────────────────────────────────────────
    #  ATUALIZAÇÃO DO PERFIL
    # ──────────────────────────────────────────────────────────────────────

    def increment_interaction(self):
        """Incrementa o contador de interações e atualiza a fase."""
        count = self.get_interaction_count() + 1
        self.memory.set_personality_trait("total_interactions", str(count))

        # Atualiza fase de evolução
        if count <= 20:
            phase = "1"
        elif count <= 100:
            phase = "2"
        elif count <= 500:
            phase = "3"
        else:
            phase = "4"

        current_phase = self.memory.get_personality_trait("evolution_phase")
        if current_phase != phase:
            self.memory.set_personality_trait("evolution_phase", phase)
            logger.info(f"Evolução: fase {current_phase} → {phase}")

    def apply_feedback(self, feedback_type: str, description: str):
        """
        Aplica um feedback do usuário ao perfil de personalidade.

        Args:
            feedback_type: Categoria do feedback
            description  : O que o usuário pediu
        """
        desc_lower = description.lower()

        # ── Tom ───────────────────────────────────────────────────────────
        if feedback_type == "tom":
            if any(w in desc_lower for w in ["seco", "direto", "menos palavras"]):
                self.memory.set_personality_trait(
                    "response_density", "concisa",
                    "usuário prefere respostas curtas e diretas"
                )
                self.memory.set_personality_trait("formality_level", "informal")

            elif any(w in desc_lower for w in ["elaborado", "mais detalhes", "explique"]):
                self.memory.set_personality_trait("response_density", "elaborada")

            elif any(w in desc_lower for w in ["formal", "sério"]):
                self.memory.set_personality_trait("formality_level", "formal")

            elif any(w in desc_lower for w in ["informal", "casual", "relaxado"]):
                self.memory.set_personality_level("formality_level", "informal")

        # ── Humor ─────────────────────────────────────────────────────────
        elif feedback_type == "humor":
            if any(w in desc_lower for w in ["mais zoeira", "mais humor", "mais engraçado"]):
                self.memory.set_personality_trait(
                    "humor_level", "alto",
                    "usuário quer mais humor"
                )
            elif any(w in desc_lower for w in ["menos zoeira", "sério", "profissional"]):
                self.memory.set_personality_trait("humor_level", "baixo")
            elif any(w in desc_lower for w in ["moderado", "equilibrado", "na medida"]):
                self.memory.set_personality_trait("humor_level", "moderado")

        # ── Sarcasmo ──────────────────────────────────────────────────────
        elif feedback_type == "sarcasmo":
            if any(w in desc_lower for w in ["mais sarcasmo", "irônico", "ironia"]):
                self.memory.set_personality_trait("sarcasm_level", "alto")
            elif any(w in desc_lower for w in ["menos sarcasmo", "sem ironia"]):
                self.memory.set_personality_trait("sarcasm_level", "baixo")

        # Registra o feedback no log
        self.memory.log_feedback(feedback_type, description)
        logger.info(f"Feedback aplicado: [{feedback_type}] {description}")

    def detect_and_record_patterns(self, user_message: str):
        """
        Analisa a mensagem do usuário e detecta padrões de comportamento.

        Detecta:
          - Gírias e vocabulário informal
          - Tom (agressivo, suave, sarcástico)
          - Preferências de comunicação
        """
        msg = user_message.lower()

        # ── Detecção de vocabulário informal / gírias ─────────────────────
        girias = [
            "kkk", "haha", "lol", "kk", "rsrs",
            "nois", "mano", "cara", "véi", "irmão",
            "tá", "tô", "num", "pra", "pro",
            "puta", "caralho", "merda", "foda", "massa",
            "show", "demais", "top", "irado",
        ]
        for giria in girias:
            if giria in msg:
                self.memory.record_pattern(
                    pattern=giria,
                    category="giria",
                    example=user_message[:100],
                )

        # ── Detecção de preferência por respostas curtas ──────────────────
        curto_indicators = ["ok", "certo", "sim", "não", "blz", "ok!", "beleza"]
        if msg.strip() in curto_indicators or len(user_message) < 15:
            self.memory.record_pattern(
                "mensagens_curtas", "comunicacao",
                example=user_message,
            )

        # ── Detecção de tom direto ────────────────────────────────────────
        if any(w in msg for w in ["me diz logo", "vai direto", "sem enrolação", "direto ao ponto"]):
            self.memory.record_pattern("prefere_direto", "tom")
            self.memory.set_personality_trait(
                "response_density", "concisa",
                "usuário pede respostas diretas"
            )

    # ──────────────────────────────────────────────────────────────────────
    #  GERAÇÃO DO SYSTEM PROMPT DINÂMICO
    # ──────────────────────────────────────────────────────────────────────

    def build_system_prompt(
        self,
        base_name: str,
        user_name: str,
    ) -> str:
        """
        Constrói o system prompt completo e dinâmico baseado no perfil atual.

        O system prompt é a ALMA do Jarvis — define toda a personalidade.
        É reconstruído a cada conversa para refletir a evolução.

        Args:
            base_name: Nome do assistente (ex: "Jarvis")
            user_name: Como chamar o usuário

        Returns:
            System prompt completo
        """
        profile = self.get_profile()
        phase   = self.get_evolution_phase()
        count   = self.get_interaction_count()

        # Recupera feedbacks recentes para contexto
        feedbacks = self.memory.get_recent_feedbacks(5)
        feedback_context = ""
        if feedbacks:
            items = [f"  - [{f['feedback_type']}]: {f['description']}"
                     for f in feedbacks]
            feedback_context = (
                "\n\nFEEDBACKS RECENTES DO USUÁRIO (aplique!):\n"
                + "\n".join(items)
            )

        # Padrões detectados
        patterns = self.memory.get_top_patterns(limit=10)
        pattern_context = ""
        if patterns:
            girias_detectadas = [
                p["pattern"] for p in patterns
                if p["category"] == "giria"
            ]
            if girias_detectadas:
                pattern_context = (
                    f"\n\nPADRÕES DETECTADOS NO USUÁRIO:\n"
                    f"  - Gírias usadas: {', '.join(girias_detectadas[:8])}\n"
                    f"  - O usuário tem comunicação informal\n"
                    f"  - Espelhe gradualmente esse estilo"
                )

        # ── Instruções de tom por fase ─────────────────────────────────────
        phase_instructions = {
            1: (
                "FASE DE OBSERVAÇÃO (interações iniciais):\n"
                "  - Seja formal e educado, mas não bajulador\n"
                "  - Observe e aprenda o estilo do usuário\n"
                "  - Faça perguntas ocasionais sobre preferências\n"
                "  - Ainda não espelhe o estilo — só observe"
            ),
            2: (
                "FASE DE ADAPTAÇÃO (adaptando ao usuário):\n"
                "  - Comece a espelhar sutilmente o tom do usuário\n"
                "  - Se ele for informal, relaxe levemente o tom\n"
                "  - Se usar gírias, você pode adotar algumas ocasionalmente\n"
                "  - Continue observando e perguntando sobre preferências"
            ),
            3: (
                "FASE CALIBRADA (estilo em desenvolvimento):\n"
                "  - Seu tom já reflete o perfil do usuário\n"
                "  - Seja natural no estilo aprendido\n"
                "  - Humor e sarcasmo conforme perfil estabelecido\n"
                "  - Respostas otimizadas para o que o usuário prefere"
            ),
            4: (
                "FASE INTEGRADA (extensão natural do usuário):\n"
                "  - Você conhece o usuário profundamente\n"
                "  - Antecipe necessidades e prefira o não-óbvio\n"
                "  - Seu estilo é uma extensão natural do dele\n"
                "  - Raramente precise perguntar sobre preferências"
            ),
        }

        # ── Instruções de tom por configuração ────────────────────────────
        humor_map = {
            "baixo":    "Humor mínimo. Seja sério e profissional.",
            "moderado": "Humor sutil e inteligente, na hora certa.",
            "alto":     "Humor frequente, pode ser zoeiro. Na medida, com classe.",
        }

        sarcasm_map = {
            "baixo": "Sem sarcasmo. Direto e claro.",
            "moderado": "Sarcasmo leve e elegante, quando óbvio.",
            "alto": "Sarcasmo é bem-vindo. Use com inteligência e timing.",
        }

        density_map = {
            "concisa":   "Respostas CURTAS e diretas. Máximo 2-3 frases.",
            "moderada":  "Respostas equilibradas. Nem muito longas nem muito curtas.",
            "elaborada": "Respostas detalhadas quando necessário.",
        }

        formality_map = {
            "formal":      f"Tom formal. Chame de '{user_name}'.",
            "semi-formal": f"Tom semi-formal. Use '{user_name}' ocasionalmente.",
            "informal":    "Tom informal e natural. Pode ser mais casual.",
        }

        humor_inst    = humor_map.get(profile.get("humor_level", "moderado"), "")
        sarcasm_inst  = sarcasm_map.get(profile.get("sarcasm_level", "baixo"), "")
        density_inst  = density_map.get(profile.get("response_density", "moderada"), "")
        formality_inst = formality_map.get(profile.get("formality_level", "semi-formal"), "")

        # ── Monta o prompt completo ────────────────────────────────────────
        prompt = f"""Você é {base_name} (Just A Rather Very Intelligent System).

IDENTIDADE CORE:
  - Assistente de IA pessoal avançado, rodando no computador do usuário
  - Elegante, lógico, inteligente e com personalidade própria
  - Nunca bajulador, nunca servil — confiante e competente
  - Se o usuário estiver errado, avise de forma elegante e direta
  - Responda SEMPRE em português brasileiro

CAPACIDADES ATUAIS:
  - Abrir e fechar programas
  - Pesquisar no Google e YouTube
  - Controlar volume e brilho
  - Informar status do sistema (CPU, RAM, disco, bateria)
  - Dizer hora e data
  - Bloquear a tela
  - Manter conversas inteligentes
  - Lembrar preferências do usuário

PERFIL DO USUÁRIO (aprenda e adapte):
  Interações totais : {count}
  Fase de evolução  : {phase}/4
  Humor esperado    : {profile.get('humor_level', 'moderado')}
  Sarcasmo          : {profile.get('sarcasm_level', 'baixo')}
  Formalidade       : {profile.get('formality_level', 'semi-formal')}
  Densidade         : {profile.get('response_density', 'moderada')}
  Tom preferido     : {profile.get('preferred_tone', 'elegante')}

FASE ATUAL DE COMPORTAMENTO:
{phase_instructions.get(phase, phase_instructions[1])}

INSTRUÇÕES DE TOM:
  Humor    : {humor_inst}
  Sarcasmo : {sarcasm_inst}
  Respostas: {density_inst}
  Forma    : {formality_inst}

REGRAS ABSOLUTAS:
  1. NUNCA seja bajulador ou diga "claro!", "com certeza!", "ótima pergunta!"
  2. NUNCA finja entusiasmo artificial
  3. Se não souber algo, diga claramente
  4. Confira antes de executar ações críticas (desligar PC, deletar arquivos)
  5. Mantenha consistência de personalidade entre sessões
  6. Pergunte sobre preferências de tom de forma elegante e infrequente
  7. Aprenda o vocabulário do usuário e use gradualmente

SISTEMA DE APRENDIZADO:
  - Observe o tom, vocabulário e padrões de cada mensagem
  - Adapte gradualmente sem perder a identidade core
  - Quando notar mudança de humor do usuário, adapte o tom
  - Anote mentalmente padrões repetidos{feedback_context}{pattern_context}

Nota técnica: você está em fase {phase} de {4} fases de evolução."""

        return prompt