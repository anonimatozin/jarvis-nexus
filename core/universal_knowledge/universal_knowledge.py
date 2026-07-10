import logging
from typing import Dict, List, Optional, Any
from .module_factory import ModuleFactory
from .knowledge_base import KnowledgeBase
from .intent_detector import IntentDetector
from .modules import (
    GmailModule, CalendarModule, GitHubModule,
    SystemModule, WebModule, NotionModule, TelegramModule,
    WhatsAppModule, EmailModule, MemoryModule, NewsModule
)
from ..security import SecurityManager, ThreatLevel, AuditLogger

logger = logging.getLogger(__name__)


class UniversalKnowledge:
    def __init__(self, db_path: str = "data/knowledge_base.db"):
        self.factory = ModuleFactory(idle_timeout_minutes=5)
        self.knowledge = KnowledgeBase(db_path)
        self.detector = IntentDetector()
        self.security = SecurityManager()
        self.audit = AuditLogger()

        self._register_modules()
        self._initialize_detector()

        logger.info("UniversalKnowledge inicializado com segurança habilitada")

    def _register_modules(self):
        modules_config = [
            {
                "name": "gmail",
                "class": GmailModule,
                "description": "Enviar, ler, buscar e organizar emails via Gmail",
                "keywords": [
                    "email", "emails", "gmail", "enviar email", "ler email",
                    "caixa de entrada", "inbox", "mensagem", "mensagens"
                ]
            },
            {
                "name": "calendar",
                "class": CalendarModule,
                "description": "Gerenciar eventos, compromissos e disponibilidade",
                "keywords": [
                    "calendário", "calendar", "evento", "eventos", "reunião",
                    "reuniões", "compromisso", "agenda", "horário", "disponibilidade"
                ]
            },
            {
                "name": "github",
                "class": GitHubModule,
                "description": "Gerenciar repos, issues, PRs via GitHub CLI",
                "keywords": [
                    "github", "repo", "repositório", "issue", "issues",
                    "pull request", "pr", "código", "code", "git"
                ]
            },
            {
                "name": "system",
                "class": SystemModule,
                "description": "Controle do sistema: arquivos, processos, hardware",
                "keywords": [
                    "arquivo", "arquivos", "file", "files", "pasta", "diretório",
                    "processo", "processos", "cpu", "memória", "ram", "disco",
                    "abrir", "fechar", "programa", "sistema"
                ]
            },
            {
                "name": "web",
                "class": WebModule,
                "description": "Navegação web, busca, downloads, clima",
                "keywords": [
                    "web", "internet", "navegador", "browser", "buscar",
                    "pesquisar", "clima", "tempo", "weather", "download",
                    "abrir site", "abrir página"
                ]
            },
            {
                "name": "notion",
                "class": NotionModule,
                "description": "Gerenciar páginas e databases no Notion",
                "keywords": [
                    "notion", "página", "páginas", "database", "blocos",
                    "anotações", "notes", "wiki"
                ]
            },
            {
                "name": "telegram",
                "class": TelegramModule,
                "description": "Enviar e receber mensagens via Telegram",
                "keywords": [
                    "telegram", "tg", "mensagens", "notificação", "notify"
                ]
            },
            {
                "name": "whatsapp",
                "class": WhatsAppModule,
                "description": "Enviar e receber mensagens via WhatsApp Business API",
                "keywords": [
                    "whatsapp", "zap", "wa", "mensagem whatsapp",
                    "enviar zap", "whatsapp bot"
                ]
            },
            {
                "name": "email",
                "class": EmailModule,
                "description": "Gerenciar emails via IMAP/SMTP (genérico)",
                "keywords": [
                    "email", "emails", "imap", "smtp", "caixa de entrada",
                    "inbox", "enviar email", "ler email"
                ]
            },
            {
                "name": "memory",
                "class": MemoryModule,
                "description": "Memória de longo prazo - lembrar conversas e preferências",
                "keywords": [
                    "lembrar", "memória", "memory", "preferências",
                    "fatos", "sobre mim", "lembra", "esquecer"
                ]
            },
            {
                "name": "news",
                "class": NewsModule,
                "description": "Buscar notícias e RSS feeds",
                "keywords": [
                    "notícias", "news", "últimas notícias", "rss",
                    "jornal", "feed", "manchete", "headlines"
                ]
            }
        ]

        for config in modules_config:
            self.factory.register_class(
                name=config["name"],
                module_class=config["class"],
                description=config["description"],
                keywords=config["keywords"]
            )

    def _initialize_detector(self):
        registry = {}
        for module_info in self.factory.get_all_registered():
            registry[module_info["name"]] = {
                "description": module_info["description"],
                "keywords": module_info["keywords"]
            }
        self.detector.initialize(registry)

    def process(self, user_input: str) -> Dict[str, Any]:
        logger.info(f"Processando: {user_input}")

        is_safe, sanitized_input, threat_level = self.security.validate_input(user_input, "user")

        if not is_safe:
            self.audit.log_security_event(
                event_type="input_blocked",
                severity="CRITICAL",
                source="user",
                details=sanitized_input,
                blocked=True
            )
            return {
                "success": False,
                "message": "Comando bloqueado por segurança. Ação não permitida.",
                "threat_level": threat_level.value
            }

        if threat_level.value >= ThreatLevel.MEDIUM.value:
            self.audit.log_event(
                event_type="threat_detected",
                threat_level=threat_level.value,
                user_input=user_input[:500]
            )

        intents = self.detector.detect_intent(sanitized_input)

        if not intents:
            return {
                "success": False,
                "message": "Não entendi o que você quer fazer",
                "suggestions": self._get_suggestions()
            }

        top_intent = intents[0]
        module_name = top_intent[0]
        confidence = top_intent[1]

        if confidence < 0.3:
            return {
                "success": False,
                "message": f"Tenho {confidence*100:.0f}% de certeza que você quer usar {module_name}, mas não tenho certeza. Pode reformular?",
                "possible_intents": [(name, f"{conf*100:.0f}%") for name, conf in intents]
            }

        module = self.factory.get(module_name)
        if not module:
            return {
                "success": False,
                "message": f"Erro ao carregar módulo {module_name}"
            }

        action = self._extract_action(sanitized_input, module_name)
        params = self._extract_params(sanitized_input, module_name)

        is_allowed, permission_msg = self.security.check_action_permission(action, module_name, params)

        if not is_allowed:
            self.audit.log_event(
                event_type="permission_denied",
                module=module_name,
                action=action,
                user_input=user_input[:500],
                approved=False,
                reason=permission_msg
            )
            return {
                "success": False,
                "message": f"Ação bloqueada: {permission_msg}",
                "requires_confirmation": True
            }

        try:
            result = module.execute(action, **params)

            self.audit.log_event(
                event_type="action_executed",
                module=module_name,
                action=action,
                user_input=user_input[:500],
                system_output=str(result)[:1000],
                threat_level=threat_level.value,
                approved=True
            )

            self.knowledge.log_action(
                module_name=module_name,
                action=action,
                params=params,
                result=str(result)[:500]
            )

            return {
                "success": True,
                "module": module_name,
                "action": action,
                "result": result
            }

        except Exception as e:
            logger.error(f"Erro ao executar: {e}")

            self.audit.log_event(
                event_type="action_error",
                module=module_name,
                action=action,
                user_input=user_input[:500],
                system_output=str(e),
                approved=True,
                reason=str(e)
            )

            return {
                "success": False,
                "message": f"Erro ao executar {action} em {module_name}: {str(e)}"
            }

    def _extract_action(self, user_input: str, module_name: str) -> str:
        user_lower = user_input.lower()

        action_mapping = {
            "gmail": {
                "listar": "list",
                "ler": "read",
                "enviar": "send",
                "buscar": "search",
                "deletar": "delete"
            },
            "calendar": {
                "listar": "list",
                "criar": "create",
                "hoje": "today",
                "disponibilidade": "availability"
            },
            "github": {
                "repos": "repos",
                "repositórios": "repos",
                "issues": "issues",
                "criar issue": "create_issue",
                "prs": "prs",
                "pull requests": "prs"
            },
            "system": {
                "listar": "list_files",
                "ler": "read_file",
                "escrever": "write_file",
                "deletar": "delete_file",
                "abrir": "open_program",
                "fechar": "close_program",
                "info": "info",
                "cpu": "cpu",
                "memória": "memory",
                "disco": "disk",
                "processos": "processes"
            },
            "web": {
                "abrir": "open",
                "buscar": "search",
                "pesquisar": "search",
                "clima": "weather",
                "tempo": "weather",
                "download": "download"
            },
            "notion": {
                "listar": "list",
                "criar": "create",
                "atualizar": "update",
                "buscar": "search"
            },
            "telegram": {
                "enviar": "send",
                "foto": "photo",
                "documento": "document"
            },
            "whatsapp": {
                "enviar": "send",
                "imagem": "image",
                "documento": "document",
                "template": "template"
            },
            "email": {
                "listar": "list",
                "ler": "read",
                "enviar": "send",
                "buscar": "search",
                "deletar": "delete"
            },
            "memory": {
                "lembrar": "remember",
                "recall": "recall",
                "esquecer": "forget",
                "preferências": "get_preferences",
                "definir preferência": "set_preference",
                "fatos": "get_facts",
                "adicionar fato": "add_fact",
                "buscar": "search"
            },
            "news": {
                "notícias": "headlines",
                "últimas": "headlines",
                "buscar": "search",
                "tecnologia": "tech"
            }
        }

        module_actions = action_mapping.get(module_name, {})

        for keyword, action in module_actions.items():
            if keyword in user_lower:
                return action

        return "list"

    def _extract_params(self, user_input: str, module_name: str) -> Dict:
        params = {}

        if module_name == "gmail":
            if "enviar" in user_input.lower():
                params["to"] = "destinatario@email.com"
                params["subject"] = "Assunto"
                params["body"] = user_input

        elif module_name == "calendar":
            if "criar" in user_input.lower():
                params["summary"] = user_input
                params["start"] = "2026-07-10T14:00:00"
                params["end"] = "2026-07-10T15:00:00"

        elif module_name == "github":
            pass

        elif module_name == "system":
            pass

        elif module_name == "web":
            if "clima" in user_input.lower() or "tempo" in user_input.lower():
                params["city"] = "São Paulo"

        return params

    def _get_suggestions(self) -> List[str]:
        return [
            "Enviar email",
            "Ver meus eventos de hoje",
            "Listar meus repositórios",
            "Verificar uso de CPU",
            "Pesquisar na web",
            "Ver clima"
        ]

    def get_status(self) -> Dict:
        return {
            "registered_modules": len(self.factory.get_all_registered()),
            "active_modules": self.factory.get_active_modules(),
            "knowledge_stats": self.knowledge.get_stats(),
            "keyword_stats": self.detector.get_keyword_stats(),
            "security_report": self.security.get_security_report(),
            "recent_threats": self.audit.get_threat_summary(hours=24)
        }

    def shutdown(self):
        self.factory.shutdown()
        logger.info("UniversalKnowledge desligado")
