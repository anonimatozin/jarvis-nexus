"""
Self-Evolving Skills System
Inspirado no GenericAgent - crystalliza tarefas em skills reutilizaveis.
"""
import json
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import threading


class SkillEvolver:
    """
    Sistema de auto-evolucao de skills.
    Aprende com tarefas executadas e cria skills reutilizaveis.
    """
    
    def __init__(self, skills_dir: str = None):
        self.skills_dir = Path(skills_dir or "data/skills")
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        self.skills_index = self.skills_dir / "skills_index.json"
        self.execution_log = self.skills_dir / "execution_log.json"
        
        self._skills = self._load_skills()
        self._log = self._load_log()
        self._lock = threading.Lock()
        
        print(f"[SKILLS] {len(self._skills)} skills carregadas")
    
    def _load_skills(self) -> Dict:
        if self.skills_index.exists():
            try:
                with open(self.skills_index, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_skills(self):
        try:
            with open(self.skills_index, "w", encoding="utf-8") as f:
                json.dump(self._skills, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[SKILLS] Erro salvar: {e}")
    
    def _load_log(self) -> List:
        if self.execution_log.exists():
            try:
                with open(self.execution_log, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def _save_log(self):
        try:
            if len(self._log) > 1000:
                self._log = self._log[-1000:]
            with open(self.execution_log, "w", encoding="utf-8") as f:
                json.dump(self._log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[SKILLS] Erro salvar log: {e}")
    
    def _gerar_skill_id(self, nome: str, comandos: List[str]) -> str:
        content = nome + "".join(sorted(comandos))
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def registrar_execucao(self, comando: str, resultado: str, 
                          sucesso: bool, contexto: Dict = None):
        registro = {
            "timestamp": datetime.now().isoformat(),
            "comando": comando,
            "resultado": resultado[:200],
            "sucesso": sucesso,
            "contexto": contexto or {}
        }
        
        with self._lock:
            self._log.append(registro)
            self._save_log()
            
            if len(self._log) % 10 == 0:
                self._analisar_padroes()
    
    def _analisar_padroes(self):
        contagem = {}
        for reg in self._log[-100:]:
            cmd = reg["comando"].lower().strip()
            cmd_normalizado = self._normalizar_comando(cmd)
            if cmd_normalizado not in contagem:
                contagem[cmd_normalizado] = {"count": 0, "exemplos": []}
            contagem[cmd_normalizado]["count"] += 1
            if len(contagem[cmd_normalizado]["exemplos"]) < 3:
                contagem[cmd_normalizado]["exemplos"].append(cmd)
        
        for cmd, dados in contagem.items():
            if dados["count"] >= 3:
                if not self._skill_existe(cmd):
                    self._criar_skill_automatica(cmd, dados)
    
    def _normalizar_comando(self, cmd: str) -> str:
        cmd = re.sub(r'\d+', 'N', cmd)
        cmd = re.sub(r'\b(o|a|os|as|de|do|da|no|na|em|para|por|com)\b', '', cmd)
        cmd = re.sub(r'\s+', ' ', cmd).strip()
        return cmd
    
    def _skill_existe(self, cmd_normalizado: str) -> bool:
        for skill in self._skills.values():
            if skill.get("padrao_normalizado") == cmd_normalizado:
                return True
            for padrao in skill.get("padroes", []):
                if self._normalizar_comando(padrao) == cmd_normalizado:
                    return True
        return False
    
    def _criar_skill_automatica(self, cmd: str, dados: Dict):
        nome = f"auto_{cmd[:30].replace(' ', '_')}"
        skill_id = self._gerar_skill_id(nome, dados["exemplos"])
        
        skill = {
            "id": skill_id,
            "nome": nome,
            "tipo": "auto",
            "criada_em": datetime.now().isoformat(),
            "execucoes": dados["count"],
            "padroes": dados["exemplos"],
            "padrao_normalizado": cmd,
            "comando_template": cmd,
            "confianca": min(0.5 + (dados["count"] * 0.1), 0.95)
        }
        
        self._skills[skill_id] = skill
        self._save_skills()
        print(f"[SKILLS] Skill auto-criada: {nome} (conf: {skill['confianca']:.0%})")
    
    def criar_skill_manual(self, nome: str, padroes: List[str], 
                          acoes: List[Dict], descricao: str = "") -> str:
        skill_id = self._gerar_skill_id(nome, padroes)
        
        skill = {
            "id": skill_id,
            "nome": nome,
            "tipo": "manual",
            "criada_em": datetime.now().isoformat(),
            "descricao": descricao,
            "padroes": padroes,
            "acoes": acoes,
            "confianca": 0.9
        }
        
        self._skills[skill_id] = skill
        self._save_skills()
        print(f"[SKILLS] Skill manual criada: {nome}")
        return skill_id
    
    def buscar_skill(self, comando: str) -> Optional[Dict]:
        cmd_lower = comando.lower().strip()
        cmd_norm = self._normalizar_comando(cmd_lower)
        
        melhor_match = None
        melhor_score = 0
        
        for skill in self._skills.values():
            for padrao in skill.get("padroes", []):
                padrao_norm = self._normalizar_comando(padrao.lower())
                
                if cmd_norm == padrao_norm:
                    return skill
                
                if padrao.lower() in cmd_lower or cmd_lower in padrao.lower():
                    score = skill.get("confianca", 0.5)
                    if score > melhor_score:
                        melhor_score = score
                        melhor_match = skill
        
        if melhor_match and melhor_score >= 0.6:
            return melhor_match
        
        return None
    
    def listar_skills(self) -> List[Dict]:
        return list(self._skills.values())
    
    def remover_skill(self, skill_id: str) -> bool:
        if skill_id in self._skills:
            del self._skills[skill_id]
            self._save_skills()
            return True
        return False
    
    def get_stats(self) -> Dict:
        return {
            "total_skills": len(self._skills),
            "skills_manuais": sum(1 for s in self._skills.values() if s.get("tipo") == "manual"),
            "skills_auto": sum(1 for s in self._skills.values() if s.get("tipo") == "auto"),
            "total_execucoes_log": len(self._log),
            "ultima_execucao": self._log[-1]["timestamp"] if self._log else None
        }


_evolver_instance = None

def get_skill_evolver(skills_dir: str = None) -> SkillEvolver:
    global _evolver_instance
    if _evolver_instance is None:
        _evolver_instance = SkillEvolver(skills_dir)
    return _evolver_instance
