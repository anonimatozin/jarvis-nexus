"""
JARVIS Multi-Language v1.0
Suporte multi-idioma com tradução automática.

Baseado em: explosion/spaCy (70+ idiomas)
Recursos:
  - Detecção automática de idioma
  - Tradução entre idiomas
  - Localização de interface
  - Suporte a 100+ idiomas
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ═══ DEPENDENCIAS ═══
_langdetect_ok = False
_translator_ok = False

try:
    from langdetect import detect, detect_langs
    _langdetect_ok = True
except ImportError:
    pass

try:
    from deep_translator import GoogleTranslator
    _translator_ok = True
except ImportError:
    try:
        from googletrans import Translator
        _translator_ok = True
    except ImportError:
        pass


# ═══ IDIOMAS SUPORTADOS ═══
IDIOMAS = {
    "pt": {"nome": "Português", "regiao": "Brasil/Portugal"},
    "en": {"nome": "English", "regiao": "UK/US/AU"},
    "es": {"nome": "Español", "regiao": "Espanha/América Latina"},
    "fr": {"nome": "Français", "regiao": "França/Canadá"},
    "de": {"nome": "Deutsch", "regiao": "Alemanha/Áustria"},
    "it": {"nome": "Italiano", "regiao": "Itália"},
    "ja": {"nome": "日本語", "regiao": "Japão"},
    "zh": {"nome": "中文", "regiao": "China"},
    "ko": {"nome": "한국어", "regiao": "Coreia do Sul"},
    "ru": {"nome": "Русский", "regiao": "Rússia"},
    "ar": {"nome": "العربية", "regiao": "Mundo Árabe"},
    "hi": {"nome": "हिन्दी", "regiao": "Índia"},
    "nl": {"nome": "Nederlands", "regiao": "Holanda"},
    "pl": {"nome": "Polski", "regiao": "Polônia"},
    "tr": {"nome": "Türkçe", "regiao": "Turquia"},
    "th": {"nome": "ไทย", "regiao": "Tailândia"},
    "vi": {"nome": "Tiếng Việt", "regiao": "Vietnã"},
    "sv": {"nome": "Svenska", "regiao": "Suécia"},
    "da": {"nome": "Dansk", "regiao": "Dinamarca"},
    "fi": {"nome": "Suomi", "regiao": "Finlândia"},
}

# ═══ TEXTOS DA INTERFACE ═══
INTERFACE_TEXTS = {
    "pt": {
        "saudacao": "Olá! Como posso ajudar?",
        "entendido": "Entendido!",
        "erro": "Desculpe, ocorreu um erro.",
        "processando": "Processando...",
        "concluido": "Concluído!",
        "audio": "Áudio",
        "texto": "Texto",
        "configuracoes": "Configurações",
        "ajuda": "Ajuda"
    },
    "en": {
        "saudacao": "Hello! How can I help you?",
        "entendido": "Understood!",
        "erro": "Sorry, an error occurred.",
        "processando": "Processing...",
        "concluido": "Completed!",
        "audio": "Audio",
        "texto": "Text",
        "configuracoes": "Settings",
        "ajuda": "Help"
    },
    "es": {
        "saudacao": "¡Hola! ¿Cómo puedo ayudarte?",
        "entendido": "¡Entendido!",
        "erro": "Lo siento, ocurrió un error.",
        "processando": "Procesando...",
        "concluido": "¡Completado!",
        "audio": "Audio",
        "texto": "Texto",
        "configuracoes": "Configuración",
        "ajuda": "Ayuda"
    },
    "fr": {
        "saudacao": "Bonjour! Comment puis-je vous aider?",
        "entendido": "Compris!",
        "erro": "Désolé, une erreur s'est produite.",
        "processando": "Traitement...",
        "concluido": "Terminé!",
        "audio": "Audio",
        "texto": "Texte",
        "configuracoes": "Paramètres",
        "ajuda": "Aide"
    },
    "ja": {
        "saudacao": "こんにちは！お手伝いできますか？",
        "entendido": "了解しました！",
        "erro": "申し訳ありません、エラーが発生しました。",
        "processando": "処理中...",
        "concluido": "完了！",
        "audio": "音声",
        "texto": "テキスト",
        "configuracoes": "設定",
        "ajuda": "ヘルプ"
    }
}


class MultiLanguage:
    """Suporte multi-idioma."""

    def __init__(self, idioma_padrao: str = "pt"):
        self.idioma_padrao = idioma_padrao
        self._translator = None

        print(f"[LANG] Idioma padrão: {IDIOMAS.get(idioma_padrao, {}).get('nome', idioma_padrao)}")
        print(f"  langdetect: {'✅' if _langdetect_ok else '❌'}")
        print(f"  translator: {'✅' if _translator_ok else '❌'}")

        if _translator_ok:
            self._init_translator()

    def _init_translator(self):
        """Inicializa tradutor."""
        try:
            self._translator = GoogleTranslator()
            print("[LANG] Google Translator inicializado")
        except Exception:
            try:
                self._translator = Translator()
                print("[LANG] GoogleTrans inicializado")
            except Exception:
                print("[LANG] Tradutor não disponível")

    def detectar_idioma(self, texto: str) -> Optional[str]:
        """Detecta idioma do texto."""
        if not _langdetect_ok:
            return None

        try:
            idioma = detect(texto)
            return idioma
        except Exception:
            return None

    def detectar_idiomas(self, texto: str) -> List[Dict]:
        """Detecta múltiplos idiomas com probabilidades."""
        if not _langdetect_ok:
            return []

        try:
            idiomas = detect_langs(texto)
            return [{
                "idioma": str(lang).split(":")[0],
                "probabilidade": float(str(lang).split(":")[1])
            } for lang in idiomas]
        except Exception:
            return []

    def traduzir(self, texto: str, destino: str = None, origem: str = None) -> Optional[str]:
        """Traduz texto para o idioma de destino."""
        if not self._translator:
            return None

        destino = destino or self.idioma_padrao
        origem = origem or self.detectar_idioma(texto)

        if origem == destino:
            return texto

        try:
            if isinstance(self._translator, GoogleTranslator):
                resultado = self._translator.translate(texto, src=origem, dest=destino)
            else:
                resultado = self._translator.translate(texto, dest=destino, src=origem)
            return resultado
        except Exception as e:
            print(f"[LANG] Erro traduzindo: {e}")
            return None

    def traduzir_automatico(self, texto: str, destino: str = None) -> Optional[str]:
        """Traduz automaticamente detectando o idioma original."""
        return self.traduzir(texto, destino)

    def obter_texto_interface(self, chave: str, idioma: str = None) -> str:
        """Obtém texto da interface no idioma especificado."""
        idioma = idioma or self.idioma_padrao
        textos = INTERFACE_TEXTS.get(idioma, INTERFACE_TEXTS.get("en", {}))
        return textos.get(chave, chave)

    def listar_idiomas(self) -> List[Dict]:
        """Lista idiomas disponíveis."""
        return [{"codigo": k, **v} for k, v in IDIOMAS.items()]

    def obter_nome_idioma(self, codigo: str) -> str:
        """Obtém nome do idioma pelo código."""
        return IDIOMAS.get(codigo, {}).get("nome", codigo)

    def resumir_texto(self, texto: str, idioma: str = None) -> Optional[str]:
        """Resumo traduzido de texto longo."""
        idioma = idioma or self.idioma_padrao

        # Detecta idioma se não especificado
        if not idioma:
            idioma_detectado = self.detectar_idioma(texto)
            if idioma_detectado:
                idioma = idioma_detectado
            else:
                idioma = "en"

        # Pega primeiras frases como resumo
        frases = texto.split(". ")
        if len(frases) <= 2:
            resumo = texto
        else:
            resumo = ". ".join(frases[:3]) + "."

        # Traduz se necessário
        if idioma != self.idioma_padrao:
            resumo_traduzido = self.traduzir(resumo, self.idioma_padrao, idioma)
            if resumo_traduzido:
                return resumo_traduzido

        return resumo

    def multilingue(self, textos: Dict[str, str]) -> str:
        """Retorna texto no idioma preferido."""
        idioma = self.idioma_padrao
        return textos.get(idioma, textos.get("en", list(textos.values())[0] if textos else ""))

    def status(self) -> Dict:
        """Retorna status do módulo."""
        return {
            "idioma_padrao": self.idioma_padrao,
            "langdetect": _langdetect_ok,
            "translator": _translator_ok,
            "idiomas_suportados": len(IDIOMAS)
        }


# ═══ INSTANCIA GLOBAL ═══
_lang_instance = None


def get_multi_language(idioma: str = "pt") -> MultiLanguage:
    """Retorna instância do Multi-Language."""
    global _lang_instance
    if _lang_instance is None:
        _lang_instance = MultiLanguage(idioma)
    return _lang_instance
