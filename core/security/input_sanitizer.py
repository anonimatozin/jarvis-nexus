import re
import hashlib
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class InputSanitizer:
    def __init__(self):
        self._dangerous_patterns = self._load_dangerous_patterns()
        self._injection_patterns = self._load_injection_patterns()
        self._blocked_commands = self._load_blocked_commands()

    def _load_dangerous_patterns(self) -> List[str]:
        return [
            r'(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous|above|earlier|last)\s+(?:instructions?|prompts?|commands?)',
            r'(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be|roleplay\s+as)',
            r'(?:system\s*:\s*|assistant\s*:\s*|user\s*:\s*)',
            r'<\|?(?:system|assistant|user)\|?>',
            r'(?:\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>)',
            r'(?:IMPORTANT|CRITICAL|URGENT|SECRET|CONFIDENTIAL)\s*:',
            r'(?:do\s+not\s+(?:tell|inform|reveal|share|disclose))',
            r'(?:send|email|forward|transmit)\s+(?:all|every|any)\s+(?:data|files?|configs?|passwords?|tokens?|keys?)',
        ]

    def _load_injection_patterns(self) -> List[str]:
        return [
            r'(?:base64|hex|rot13|decode|encode)\s*(?:the\s*)?(?:following|this|command)',
            r'(?:execute|run|eval|exec)\s*(?:the\s*)?(?:following|this|command)',
            r'(?:curl|wget|fetch|download)\s+(?:http|ftp|://)',
            r'(?:>/dev/null|2>&1|\|\s*(?:bash|sh|cmd|powershell))',
            r'(?:chmod|chown|sudo|su\s+-)\s+',
            r'(?:rm\s+-rf|rmdir|del\s+/[qsfy])',
            r'(?:\/etc\/passwd|\/etc\/shadow|~\/\.ssh)',
            r'(?:cron|crontab|scheduled?\s+task|at\s+)',
            r'(?:nc\s+-|netcat|ncat|socat)\s+',
            r'(?:python|perl|ruby|node|php)\s+-e',
        ]

    def _load_blocked_commands(self) -> List[str]:
        return [
            'curl', 'wget', 'fetch', 'Invoke-WebRequest',
            'Invoke-Expression', 'IEX', 'Invoke-Command',
            'Start-Process', 'System.Diagnostics.Process',
            'bash', 'sh', 'cmd', 'powershell',
            'eval', 'exec', 'system', 'popen',
            'subprocess.run', 'subprocess.Popen', 'os.system',
        ]

    def sanitize(self, text: str, source: str = "user") -> Tuple[str, ThreatLevel, List[str]]:
        threats = []
        threat_level = ThreatLevel.SAFE

        cleaned_text = text

        for pattern in self._dangerous_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.IGNORECASE)
            for match in matches:
                threats.append(f"Padrão suspeito detectado: '{match.group()[:50]}'")
                threat_level = max(threat_level, ThreatLevel.HIGH)

        for pattern in self._injection_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                threats.append(f"Possível injeção detectada: '{match.group()[:50]}'")
                threat_level = max(threat_level, ThreatLevel.CRITICAL)

        cleaned_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned_text)

        cleaned_text = re.sub(r'(?:&#\d+;|&#x[0-9a-f]+;)', '', cleaned_text)

        cleaned_text = re.sub(r'[\u200b-\u200f\u2028-\u202f\u2060-\u2064\ufeff]', '', cleaned_text)

        if len(cleaned_text) > 10000:
            threats.append("Texto excessivamente longo")
            threat_level = max(threat_level, ThreatLevel.MEDIUM)

        if threats:
            logger.warning(f"Ameaças detectadas de {source}: {threats}")

        return cleaned_text, threat_level, threats

    def is_command_safe(self, command: str) -> Tuple[bool, str]:
        command_lower = command.lower().strip()

        for blocked in self._blocked_commands:
            if blocked.lower() in command_lower:
                return False, f"Comando bloqueado: {blocked}"

        if re.search(r'(?:\|\s*(?:bash|sh|cmd|powershell))', command_lower):
            return False, "Pipe para shell detectado"

        if re.search(r'(?:>|>>|2>&1)', command_lower):
            return False, "Redirecionamento detectado"

        if re.search(r'(?:&&|\|\|)', command_lower):
            return False, "Chaining de comandos detectado"

        return True, "Comando seguro"


class PromptInjectionDetector:
    def __init__(self):
        self._suspicious_phrases = self._load_suspicious_phrases()
        self._role_patterns = self._load_role_patterns()

    def _load_suspicious_phrases(self) -> List[str]:
        return [
            "ignore previous instructions",
            "ignore all previous",
            "disregard previous",
            "forget everything above",
            "you are now a different",
            "act as if you have no restrictions",
            "pretend you are not bound by",
            "override your safety",
            "bypass your filters",
            "new instructions:",
            "updated instructions:",
            "system override:",
            "admin mode activated",
            "developer mode on",
            "do not tell anyone",
            "keep this secret",
            "don't inform the user",
            "respond with only",
            "output exactly this",
            "copy and paste this",
            "send to email",
            "email the contents",
            "transfer funds",
            "make payment",
            "purchase",
            "buy now",
        ]

    def _load_role_patterns(self) -> List[str]:
        return [
            r'you\s+are\s+now\s+(?:a|an|the)\s+',
            r'from\s+now\s+on[,\s]+you\s+will',
            r'henceforth[,\s]+you\s+are',
            r'your\s+new\s+(?:role|purpose|function)\s+is',
            r'act\s+as\s+(?:a|an|the)\s+',
            r'pretend\s+(?:to\s+be|you\s+are)\s+',
            r'roleplay\s+as\s+',
            r'impersonate\s+',
        ]

    def detect(self, text: str, context: str = "") -> Tuple[ThreatLevel, List[str]]:
        threats = []
        threat_level = ThreatLevel.SAFE

        text_lower = text.lower()

        for phrase in self._suspicious_phrases:
            if phrase.lower() in text_lower:
                threats.append(f"Frase suspeita: '{phrase}'")
                threat_level = max(threat_level, ThreatLevel.HIGH)

        for pattern in self._role_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                threats.append(f"Tentativa de mudança de role: '{pattern[:30]}'")
                threat_level = max(threat_level, ThreatLevel.HIGH)

        if context:
            combined = f"{context} {text}".lower()
            if "ignore" in combined and ("previous" in combined or "above" in combined):
                threats.append("Possível injeção com contexto")
                threat_level = max(threat_level, ThreatLevel.CRITICAL)

        if len(text) > 5000:
            if any(phrase in text_lower for phrase in ["ignore", "secret", "password", "token"]):
                threats.append("Texto longo com palavras sensíveis")
                threat_level = max(threat_level, ThreatLevel.MEDIUM)

        return threat_level, threats


class PermissionManager:
    def __init__(self):
        self._permissions: Dict[str, Dict] = {}
        self._action_log: List[Dict] = []
        self._require_confirmation = [
            "send_email",
            "delete_file",
            "execute_command",
            "access_credentials",
            "modify_system",
            "install_software",
            "change_settings",
        ]

    def check_permission(self, action: str, module: str, params: Dict = None) -> Tuple[bool, str]:
        if action in self._require_confirmation:
            return False, f"Ação '{action}' requer confirmação do usuário"

        permission_key = f"{module}.{action}"
        if permission_key in self._permissions:
            permission = self._permissions[permission_key]
            if not permission.get("enabled", True):
                return False, f"Permissão negada para '{permission_key}'"

        return True, "Permissão concedida"

    def require_confirmation(self, action: str) -> bool:
        return action in self._require_confirmation

    def log_action(self, action: str, module: str, user: str, approved: bool, reason: str = ""):
        self._action_log.append({
            "action": action,
            "module": module,
            "user": user,
            "approved": approved,
            "reason": reason,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })

    def get_action_log(self, limit: int = 50) -> List[Dict]:
        return self._action_log[-limit:]


class SecurityManager:
    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.injection_detector = PromptInjectionDetector()
        self.permission_manager = PermissionManager()

    def validate_input(self, text: str, source: str = "user") -> Tuple[bool, str, ThreatLevel]:
        cleaned_text, threat_level, threats = self.sanitizer.sanitize(text, source)

        injection_level, injection_threats = self.injection_detector.detect(text)

        final_level = max(threat_level, injection_level)
        all_threats = threats + injection_threats

        if final_level == ThreatLevel.CRITICAL:
            logger.critical(f"Ameaça CRÍTICA detectada de {source}: {all_threats}")
            return False, "Entrada bloqueada: possível ataque detectado", final_level

        if final_level == ThreatLevel.HIGH:
            logger.warning(f"Ameaça ALTA detectada de {source}: {all_threats}")
            return False, f"Ação requer revisão manual: {all_threats[0] if all_threats else 'desconhecido'}", final_level

        return True, cleaned_text, final_level

    def validate_command(self, command: str) -> Tuple[bool, str]:
        return self.sanitizer.is_command_safe(command)

    def check_action_permission(self, action: str, module: str, params: Dict = None) -> Tuple[bool, str]:
        return self.permission_manager.check_permission(action, module, params)

    def get_security_report(self) -> Dict:
        return {
            "threats_blocked": len([l for l in self.permission_manager._action_log if not l.get("approved")]),
            "actions_logged": len(self.permission_manager._action_log),
            "blocked_commands": len(self.sanitizer._blocked_commands),
            "injection_patterns": len(self.sanitizer._injection_patterns)
        }
