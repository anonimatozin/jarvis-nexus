"""
Safety Tiers System
Inspirado no JarvisAI/ThioJoe - niveis de permissao para acoes perigosas.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import hashlib


class SafetyLevel(Enum):
    SAFE = 0        # Acoes seguras, executa direto
    CAUTION = 1     # Requer confirmacao simples
    DANGER = 2      # Requer confirmacao com detalhes
    CRITICAL = 3    # Apenas com senha/autenticacao


class SafetyTiers:
    """
    Sistema de niveis de seguranca.
    Controla quais acoes precisam de confirmacao.
    """
    
    # Mapeamento de acoes para niveis
    ACTION_LEVELS = {
        # SAFE - Executa direto
        "hora_atual": SafetyLevel.SAFE,
        "data_atual": SafetyLevel.SAFE,
        "status_pc": SafetyLevel.SAFE,
        "pesquisa_web": SafetyLevel.SAFE,
        "clima": SafetyLevel.SAFE,
        "abrir_navegador": SafetyLevel.SAFE,
        
        # CAUTION - Confirmacao simples
        "app_abrir": SafetyLevel.CAUTION,
        "app_fechar": SafetyLevel.CAUTION,
        "volume_set": SafetyLevel.CAUTION,
        "brilho_set": SafetyLevel.CAUTION,
        "tocar_musica": SafetyLevel.CAUTION,
        "lembrar": SafetyLevel.CAUTION,
        "timer": SafetyLevel.CAUTION,
        
        # DANGER - Confirmacao detalhada
        "bloquear_tela": SafetyLevel.DANGER,
        "enviar_email": SafetyLevel.DANGER,
        "enviar_sms": SafetyLevel.DANGER,
        "excluir_arquivo": SafetyLevel.DANGER,
        "mover_arquivo": SafetyLevel.DANGER,
        "executar_script": SafetyLevel.DANGER,
        "tv_ligar": SafetyLevel.DANGER,
        "tv_desligar": SafetyLevel.DANGER,
        
        # CRITICAL - Senha necessaria
        "desligar_pc": SafetyLevel.CRITICAL,
        "reiniciar_pc": SafetyLevel.CRITICAL,
        "formatar": SafetyLevel.CRITICAL,
        "definir_senha": SafetyLevel.CRITICAL,
        "acesso_rede": SafetyLevel.CRITICAL,
    }
    
    def __init__(self, master_password: str = None):
        self._master_password = master_password
        self._config_file = Path("data/safety_config.json")
        self._audit_log = Path("data/safety_audit.json")
        self._approved_actions = {}
        
        self._load_config()
        print(f"[SAFETY] {len(self.ACTION_LEVELS)} acoes mapeadas")
    
    def _load_config(self):
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self._master_password = config.get("master_password_hash")
                    self._approved_actions = config.get("approved_actions", {})
            except Exception:
                pass
    
    def _save_config(self):
        try:
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump({
                    "master_password_hash": self._master_password,
                    "approved_actions": self._approved_actions
                }, f, indent=2)
        except Exception as e:
            print(f"[SAFETY] Erro salvar config: {e}")
    
    def _log_audit(self, action: str, level: SafetyLevel, 
                   approved: bool, user: str = "system"):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "level": level.name,
            "approved": approved,
            "user": user
        }
        
        try:
            log = []
            if self._audit_log.exists():
                with open(self._audit_log, "r", encoding="utf-8") as f:
                    log = json.load(f)
            
            log.append(entry)
            
            if len(log) > 500:
                log = log[-500:]
            
            with open(self._audit_log, "w", encoding="utf-8") as f:
                json.dump(log, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def get_action_level(self, action: str) -> SafetyLevel:
        for key, level in self.ACTION_LEVELS.items():
            if key in action.lower():
                return level
        return SafetyLevel.CAUTION
    
    def requires_confirmation(self, action: str) -> bool:
        level = self.get_action_level(action)
        return level.value >= SafetyLevel.CAUTION.value
    
    def requires_password(self, action: str) -> bool:
        level = self.get_action_level(action)
        return level.value >= SafetyLevel.CRITICAL.value
    
    def get_confirmation_message(self, action: str, details: Dict = None) -> Dict:
        level = self.get_action_level(action)
        
        messages = {
            SafetyLevel.SAFE: {
                "message": f"Acao segura: {action}",
                "requires_input": False
            },
            SafetyLevel.CAUTION: {
                "message": f"Confirmar acao: {action}?",
                "details": details or {},
                "requires_input": True,
                "options": ["Confirmar", "Cancelar"]
            },
            SafetyLevel.DANGER: {
                "message": f"ATENCAO: {action} e uma acao de risco!",
                "details": details or {},
                "requires_input": True,
                "options": ["Confirmo que entendo o risco", "Cancelar"],
                "warning": "Esta acao pode causar mudancas significativas"
            },
            SafetyLevel.CRITICAL: {
                "message": f"ACAO CRITICA: {action}",
                "details": details or {},
                "requires_input": True,
                "requires_password": True,
                "options": ["Digite a senha mestra para confirmar", "Cancelar"],
                "warning": "Esta acao e irreversivel!"
            }
        }
        
        return messages.get(level, messages[SafetyLevel.CAUTION])
    
    def set_master_password(self, password: str) -> bool:
        self._master_password = hashlib.sha256(password.encode()).hexdigest()
        self._save_config()
        return True
    
    def verify_master_password(self, password: str) -> bool:
        if not self._master_password:
            return True
        return hashlib.sha256(password.encode()).hexdigest() == self._master_password
    
    def approve_action(self, action: str, duration_hours: int = 24) -> bool:
        self._approved_actions[action] = {
            "approved_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        }
        self._save_config()
        self._log_audit(action, self.get_action_level(action), True)
        return True
    
    def is_approved(self, action: str) -> bool:
        if action not in self._approved_actions:
            return False
        
        approval = self._approved_actions[action]
        expires = datetime.fromisoformat(approval["expires_at"])
        
        if datetime.now() > expires:
            del self._approved_actions[action]
            self._save_config()
            return False
        
        return True
    
    def revoke_approval(self, action: str) -> bool:
        if action in self._approved_actions:
            del self._approved_actions[action]
            self._save_config()
            return True
        return False
    
    def get_audit_log(self, limit: int = 50) -> List[Dict]:
        try:
            if self._audit_log.exists():
                with open(self._audit_log, "r", encoding="utf-8") as f:
                    log = json.load(f)
                return log[-limit:]
        except Exception:
            pass
        return []
    
    def get_status(self) -> Dict:
        return {
            "total_actions_mapped": len(self.ACTION_LEVELS),
            "safe_actions": sum(1 for l in self.ACTION_LEVELS.values() if l == SafetyLevel.SAFE),
            "caution_actions": sum(1 for l in self.ACTION_LEVELS.values() if l == SafetyLevel.CAUTION),
            "danger_actions": sum(1 for l in self.ACTION_LEVELS.values() if l == SafetyLevel.DANGER),
            "critical_actions": sum(1 for l in self.ACTION_LEVELS.values() if l == SafetyLevel.CRITICAL),
            "approved_actions": len(self._approved_actions),
            "master_password_set": self._master_password is not None
        }


_tiers_instance = None

def get_safety_tiers(master_password: str = None) -> SafetyTiers:
    global _tiers_instance
    if _tiers_instance is None:
        _tiers_instance = SafetyTiers(master_password)
    return _tiers_instance
