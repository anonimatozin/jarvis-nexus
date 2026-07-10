# core/intent_parser.py
"""
J.A.R.V.I.S. - Classificador de Intenções
Analisa o texto do usuário e determina qual ação executar.

Versão 1.0: Usa correspondência por palavras-chave (rápido e offline).
Futuro: Usar modelo de NLP ou a própria IA para classificação avançada.
"""

import re
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.logger import setup_logger

logger = setup_logger("intent_parser")


class Intent:
    """Constantes de intenções reconhecidas."""
    GREETING = "greeting"
    FAREWELL = "farewell"
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    SEARCH_WEB = "search_web"
    SEARCH_YOUTUBE = "search_youtube"
    SYSTEM_INFO = "system_info"
    VOLUME_CONTROL = "volume_control"
    BRIGHTNESS_CONTROL = "brightness_control"
    TIME_DATE = "time_date"
    SHUTDOWN_PC = "shutdown_pc"
    RESTART_PC = "restart_pc"
    LOCK_SCREEN = "lock_screen"
    CONVERSATION = "conversation"  # Padrão: conversa normal
    REMEMBER = "remember"
    WHAT_CAN_YOU_DO = "capabilities"
    STATUS = "status"
    PERSONA_STATUS  = "persona_status"
    PERSONA_ADJUST  = "persona_adjust"
    OPEN_BROWSER_HUD = "open_browser_hud"
    SWITCH_THEME     = "switch_theme"
    UI_THEME_CYAN    = "ui_theme_cyan"
    UI_THEME_ORANGE  = "ui_theme_orange"
    UI_OPEN_SETTINGS = "ui_open_settings"
    UI_CLOSE_SETTINGS= "ui_close_settings"
    UI_MODE_VOICE    = "ui_mode_voice"
    UI_MODE_TEXT     = "ui_mode_text"
    UI_MODE_HYBRID   = "ui_mode_hybrid"
    UI_CLEAR_CHAT    = "ui_clear_chat"


class IntentParser:
    """
    Analisa texto e extrai intenção + entidades.
    
    Retorna:
        dict com 'intent', 'entities', 'confidence'
    """
    
    # Padrões de intenção: (intent, [padrões regex], prioridade)
    PATTERNS = [
        # Saudações
        (Intent.GREETING, [
            r'\b(olá|oi|hey|eai|e ai|bom dia|boa tarde|boa noite|hello|hi)\b'
        ], 0.8),
        
        # Despedida / Desligar Jarvis
        (Intent.FAREWELL, [
            r'\b(tchau|adeus|até logo|desligar|encerrar|sair|exit|quit|goodbye)\b',
            r'\b(pode descansar|modo espera)\b'
        ], 0.9),
        
                # Abrir HUD no navegador
        (Intent.OPEN_BROWSER_HUD, [
            r'\b(abrir|abre|mostra|exibir?)\b.*\b(interface|hud)\b.*\b(navegador|chrome|browser)\b',
            r'\b(hud|interface)\b.*\b(navegador|browser)\b',
        ], 0.95),

        # Mudar tema
        (Intent.SWITCH_THEME, [
            r'\b(muda|mudar|trocar?|altera|alterar?)\b.*\b(tema|cor|interface)\b',
            r'\b(tema|cor)\b.*\b(laranja|core|ciano|azul|cyan|ultron)\b',
            r'\b(modo)\b.*\b(core|ciano|cyan|laranja)\b',
        ], 0.95),

        # Abrir aplicativo
        (Intent.OPEN_APP, [
            r'\b(abr[aie]r?|iniciar?|executar?|rodar?|lançar?|abre|open|launch)\b\s+(.+)',
            r'\b(abra|inicie|execute|rode)\b\s+(?:o|a|os|as)?\s*(.+)',
        ], 0.9),
        
        # Fechar aplicativo
        (Intent.CLOSE_APP, [
            r'\b(fechar?|encerrar?|matar?|finalizar?|close|kill)\b\s+(?:o|a)?\s*(.+)',
        ], 0.9),
        
        # Pesquisar na web
        (Intent.SEARCH_WEB, [
            r'\b(pesquis[ae]r?|buscar?|procurar?|search|google)\b\s+(.+)',
            r'\b(pesquise|busque|procure)\b\s+(?:sobre|por)?\s*(.+)',
        ], 0.9),
        
        # Pesquisar no YouTube
        (Intent.SEARCH_YOUTUBE, [
            r'\b(youtube|vídeo|video)\b.*\b(pesquis|busc|procur|toc|play)\b\s*(.+)',
            r'\b(pesquis|busc|procur|toc|play)\b.*\b(youtube|no youtube)\b\s*(.+)',
            r'\b(tocar?|play|reproduzir?)\b\s+(.+)',
        ], 0.85),
        
        # Informações do sistema
        (Intent.SYSTEM_INFO, [
            r'\b(sistema|cpu|ram|memória|disco|bateria|processador|hardware)\b',
            r'\b(status|informações|info)\b.*\b(sistema|computador|pc|máquina)\b',
            r'\b(como está|como vai)\b.*\b(sistema|computador|pc|máquina)\b',
        ], 0.85),
        
        # Controle de volume
        (Intent.VOLUME_CONTROL, [
            r'\b(volume)\b.*\b(\d+)',
            r'\b(aumentar?|diminuir?|abaixar?|mutar?|silenciar?)\b.*\b(volume|som)\b',
            r'\b(volume|som)\b.*\b(aumentar?|diminuir?|abaixar?|mutar?|silenciar?)\b',
        ], 0.9),
        
        # Controle de brilho
        (Intent.BRIGHTNESS_CONTROL, [
            r'\b(brilho)\b.*\b(\d+)',
            r'\b(aumentar?|diminuir?|abaixar?)\b.*\b(brilho|tela)\b',
        ], 0.9),
        
        # Hora e data
        (Intent.TIME_DATE, [
            r'\b(hora|horas|horário|que horas|data|dia|hoje)\b',
        ], 0.8),
        
        # Desligar PC
        (Intent.SHUTDOWN_PC, [
            r'\b(desligar?|shutdown)\b.*\b(computador|pc|máquina)\b',
        ], 0.95),
        
        # Reiniciar PC
        (Intent.RESTART_PC, [
            r'\b(reiniciar?|restart|reboot)\b.*\b(computador|pc|máquina)\b',
        ], 0.95),
        
        # Bloquear tela
        (Intent.LOCK_SCREEN, [
            r'\b(bloquear?|lock|trancar?)\b.*\b(tela|computador|pc)\b',
        ], 0.9),
        
        # Status do Jarvis
        (Intent.STATUS, [
            r'\b(status|como você está|como vai|tudo bem)\b',
        ], 0.7),
        
        # Capacidades
        (Intent.WHAT_CAN_YOU_DO, [
            r'\b(o que você (pode|sabe|consegue)|capacidades|habilidades|funções)\b',
            r'\b(me ajud[ae]|help)\b',
        ], 0.8),
        
                # Status da personalidade
        (Intent.PERSONA_STATUS, [
            r'\b(personalidade|perfil|como você está me conhecendo|sua evolução|fase)\b',
            r'\b(o quanto você me conhece|seu perfil atual)\b',
        ], 0.85),

        # Ajuste de personalidade
        (Intent.PERSONA_ADJUST, [
            r'\b(fala mais seco|seja mais direto|menos formal|mais informal)\b',
            r'\b(mais zoeira|menos zoeira|mais humor|seja sério)\b',
            r'\b(mais sarcasmo|menos sarcasmo|pode zoar)\b',
            r'\b(resposta curta|resposta longa|vai direto)\b',
        ], 0.95),

        # Lembrar algo
        (Intent.REMEMBER, [
            r'\b(lembr[ae]r?|memoriz[ae]r?|guard[ae]r?|anot[ae]r?)\b',
            r'\b(meu nome é|eu me chamo|pode me chamar de)\b\s*(.+)',
        ], 0.85),
    ]
    
    @classmethod
    def parse(cls, text: str) -> dict:
        """
        Analisa o texto e retorna a intenção detectada.
        
        Args:
            text: Texto do usuário
            
        Returns:
            dict: {
                'intent': str,        # Tipo de intenção
                'entities': dict,     # Dados extraídos (app_name, query, etc.)
                'confidence': float,  # Confiança (0.0 a 1.0)
                'raw_text': str       # Texto original
            }
        """
        text_lower = text.lower().strip()
        
        best_match = {
            'intent': Intent.CONVERSATION,
            'entities': {},
            'confidence': 0.5,
            'raw_text': text
        }
        
        for intent, patterns, priority in cls.PATTERNS:
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    entities = cls._extract_entities(intent, text_lower, match)
                    
                    if priority > best_match['confidence']:
                        best_match = {
                            'intent': intent,
                            'entities': entities,
                            'confidence': priority,
                            'raw_text': text
                        }
        
        logger.debug(
            f"Intent: {best_match['intent']} "
            f"(conf: {best_match['confidence']}) "
            f"entities: {best_match['entities']}"
        )
        
        text_low = text.lower().strip()

        # ─── UI: Temas ───
        if any(p in text_low for p in [
            "tema azul", "tema ciano", "tema cyan", "modo azul",
            "arc reactor", "muda pra azul", "troca pra azul",
            "interface azul"
        ]):
            return {"intent": Intent.UI_THEME_CYAN, "entities": {}, "confidence": 0.95, "raw_text": text}

        if any(p in text_low for p in [
            "tema laranja", "tema dourado", "tema ouro", "tema jarvis",
            "jarvis core", "era de ultron", "modo laranja",
            "muda pra laranja", "troca pra laranja", "interface laranja",
            "interface dourada", "modo dourado"
        ]):
            return {"intent": Intent.UI_THEME_ORANGE, "entities": {}, "confidence": 0.95, "raw_text": text}

        # ─── UI: Settings ───
        if any(p in text_low for p in [
            "abrir configurações", "abre configurações", "abrir config",
            "abre config", "abrir settings", "configurações", "painel de controle",
            "abrir ajustes", "abre ajustes"
        ]):
            return {"intent": Intent.UI_OPEN_SETTINGS, "entities": {}, "confidence": 0.9, "raw_text": text}

        if any(p in text_low for p in [
            "fechar configurações", "fecha configurações", "fechar settings",
            "fecha settings", "fechar ajustes"
        ]):
            return {"intent": Intent.UI_CLOSE_SETTINGS, "entities": {}, "confidence": 0.9, "raw_text": text}

        # ─── UI: Modos ───
        if any(p in text_low for p in [
            "modo voz", "modo só voz", "apenas voz", "só voz",
            "ativar voz", "ativa voz"
        ]):
            return {"intent": Intent.UI_MODE_VOICE, "entities": {}, "confidence": 0.9, "raw_text": text}

        if any(p in text_low for p in [
            "modo texto", "modo só texto", "apenas texto", "só texto",
            "desativar voz", "desativa voz"
        ]):
            return {"intent": Intent.UI_MODE_TEXT, "entities": {}, "confidence": 0.9, "raw_text": text}

        if any(p in text_low for p in [
            "modo híbrido", "modo hibrido", "voz e texto",
            "ativar híbrido", "modo completo"
        ]):
            return {"intent": Intent.UI_MODE_HYBRID, "entities": {}, "confidence": 0.9, "raw_text": text}

        # ─── UI: Chat ───
        if any(p in text_low for p in [
            "limpar chat", "limpa chat", "limpar conversa",
            "limpa conversa", "apagar mensagens"
        ]):
            return {"intent": Intent.UI_CLEAR_CHAT, "entities": {}, "confidence": 0.9, "raw_text": text}
        
        return best_match
    
    @classmethod
    def _extract_entities(cls, intent: str, text: str, match: re.Match) -> dict:
        """
        Extrai entidades relevantes baseado na intenção.
        
        Ex: "abrir chrome" → entities: {'app_name': 'chrome'}
        """
        entities = {}
        groups = match.groups()
        
        if intent == Intent.OPEN_APP and len(groups) >= 2:
            # O app_name é o último grupo capturado
            app_name = groups[-1].strip()
            # Remove artigos
            app_name = re.sub(r'^(o|a|os|as)\s+', '', app_name).strip()
            entities['app_name'] = app_name
        
        elif intent == Intent.CLOSE_APP and len(groups) >= 2:
            entities['app_name'] = groups[-1].strip()
        
        elif intent == Intent.SEARCH_WEB and len(groups) >= 2:
            query = groups[-1].strip()
            # Remove preposições iniciais
            query = re.sub(r'^(sobre|por|de|do|da)\s+', '', query).strip()
            entities['query'] = query
        
        elif intent == Intent.SEARCH_YOUTUBE and groups:
            entities['query'] = groups[-1].strip()
        
        elif intent == Intent.VOLUME_CONTROL:
            # Tenta extrair número do volume
            num_match = re.search(r'(\d+)', text)
            if num_match:
                entities['level'] = int(num_match.group(1))
            elif 'aumentar' in text:
                entities['action'] = 'up'
            elif any(word in text for word in ['diminuir', 'abaixar']):
                entities['action'] = 'down'
            elif any(word in text for word in ['mutar', 'silenciar']):
                entities['action'] = 'mute'
        
        elif intent == Intent.BRIGHTNESS_CONTROL:
            num_match = re.search(r'(\d+)', text)
            if num_match:
                entities['level'] = int(num_match.group(1))
            elif 'aumentar' in text:
                entities['action'] = 'up'
            elif any(word in text for word in ['diminuir', 'abaixar']):
                entities['action'] = 'down'
        
        elif intent == Intent.REMEMBER:
            # Tenta extrair nome
            name_match = re.search(r'(?:meu nome é|me chamo|chamar de)\s+(\w+)', text)
            if name_match:
                entities['user_name'] = name_match.group(1).capitalize()
        
        return entities


# === Teste rápido ===
if __name__ == "__main__":
    test_phrases = [
        "Olá Jarvis",
        "Abrir o Chrome",
        "Pesquisar sobre inteligência artificial",
        "Qual o status do sistema?",
        "Volume 50",
        "Que horas são?",
        "Meu nome é Carlos",
        "Desligar o computador",
        "Como está o tempo hoje?",  # Deve ir para conversation
        "Abra o Visual Studio Code",
        "Fechar o notepad",
        "Pesquise no YouTube sobre Python",
        "Bloquear a tela",
        "Tema Laranja",
        "Limpar chat",
    ]
    
    parser = IntentParser()
    for phrase in test_phrases:
        result = parser.parse(phrase)
        print(f"  '{phrase}'")
        print(f"    → Intent: {result['intent']}, Entities: {result['entities']}, "
              f"Confidence: {result['confidence']}")
        print()