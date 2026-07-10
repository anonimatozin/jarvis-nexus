"""
Goal Pursuit System
Inspirado no vierisid/jarvis - hierarchy OKR com scoring 0.0-1.0.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum


class GoalPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class GoalStatus(Enum):
    PENDING = "pendente"
    IN_PROGRESS = "em_andamento"
    COMPLETED = "concluido"
    CANCELLED = "cancelado"
    BLOCKED = "bloqueado"


class GoalPursuit:
    """
    Sistema de perseguicao de objetivos.
    Hierarquia: Objetivo -> Resultado-Chave -> Acao Diaria
    Scoring estilo Google OKR (0.0 a 1.0)
    """
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or "data/goals")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.goals_file = self.data_dir / "goals.json"
        self._goals = self._load_goals()
        
        print(f"[GOALS] {len(self._goals)} objetivos carregados")
    
    def _load_goals(self) -> List[Dict]:
        if self.goals_file.exists():
            try:
                with open(self.goals_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def _save_goals(self):
        try:
            with open(self.goals_file, "w", encoding="utf-8") as f:
                json.dump(self._goals, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[GOALS] Erro salvar: {e}")
    
    def criar_objetivo(self, titulo: str, descricao: str = "",
                       prioridade: GoalPriority = GoalPriority.MEDIUM,
                       prazo_dias: int = 30) -> Dict:
        goal = {
            "id": len(self._goals) + 1,
            "titulo": titulo,
            "descricao": descricao,
            "prioridade": prioridade.value,
            "status": GoalStatus.PENDING.value,
            "criado_em": datetime.now().isoformat(),
            "prazo": (datetime.now() + timedelta(days=prazo_dias)).isoformat(),
            "resultados_chave": [],
            "progresso": 0.0,
            "historico": []
        }
        
        self._goals.append(goal)
        self._save_goals()
        print(f"[GOALS] Objetivo criado: {titulo}")
        return goal
    
    def adicionar_resultado_chave(self, goal_id: int, titulo: str,
                                   metrica: str = "", meta: float = 1.0) -> Optional[Dict]:
        for goal in self._goals:
            if goal["id"] == goal_id:
                kr = {
                    "id": len(goal["resultados_chave"]) + 1,
                    "titulo": titulo,
                    "metrica": metrica,
                    "meta": meta,
                    "atual": 0.0,
                    "criado_em": datetime.now().isoformat()
                }
                goal["resultados_chave"].append(kr)
                self._save_goals()
                return kr
        return None
    
    def atualizar_progresso_kr(self, goal_id: int, kr_id: int, 
                                valor: float) -> bool:
        for goal in self._goals:
            if goal["id"] == goal_id:
                for kr in goal["resultados_chave"]:
                    if kr["id"] == kr_id:
                        kr["atual"] = min(valor, kr["meta"])
                        self._calcular_progresso(goal)
                        self._save_goals()
                        return True
        return False
    
    def _calcular_progresso(self, goal: Dict):
        if not goal["resultados_chave"]:
            goal["progresso"] = 0.0
            return
        
        total = 0.0
        for kr in goal["resultados_chave"]:
            if kr["meta"] > 0:
                total += min(kr["atual"] / kr["meta"], 1.0)
        
        goal["progresso"] = total / len(goal["resultados_chave"])
    
    def get_okr_score(self, goal_id: int) -> Optional[float]:
        for goal in self._goals:
            if goal["id"] == goal_id:
                return goal["progresso"]
        return None
    
    def get_scoring_label(self, score: float) -> str:
        if score >= 0.7:
            return "Excelente"
        elif score >= 0.5:
            return "Bom"
        elif score >= 0.3:
            return "Em progresso"
        elif score > 0:
            return "Inicial"
        else:
            return "Nao iniciado"
    
    def listar_objetivos(self, status: GoalStatus = None) -> List[Dict]:
        if status:
            return [g for g in self._goals if g["status"] == status.value]
        return self._goals
    
    def get_objetivo(self, goal_id: int) -> Optional[Dict]:
        for goal in self._goals:
            if goal["id"] == goal_id:
                return goal
        return None
    
    def iniciar_objetivo(self, goal_id: int) -> bool:
        for goal in self._goals:
            if goal["id"] == goal_id:
                goal["status"] = GoalStatus.IN_PROGRESS.value
                goal["historico"].append({
                    "timestamp": datetime.now().isoformat(),
                    "acao": "iniciado"
                })
                self._save_goals()
                return True
        return False
    
    def concluir_objetivo(self, goal_id: int) -> bool:
        for goal in self._goals:
            if goal["id"] == goal_id:
                goal["status"] = GoalStatus.COMPLETED.value
                goal["progresso"] = 1.0
                goal["historico"].append({
                    "timestamp": datetime.now().isoformat(),
                    "acao": "concluido"
                })
                self._save_goals()
                return True
        return False
    
    def cancelar_objetivo(self, goal_id: int) -> bool:
        for goal in self._goals:
            if goal["id"] == goal_id:
                goal["status"] = GoalStatus.CANCELLED.value
                goal["historico"].append({
                    "timestamp": datetime.now().isoformat(),
                    "acao": "cancelado"
                })
                self._save_goals()
                return True
        return False
    
    def get_resumo(self) -> Dict:
        total = len(self._goals)
        concluidos = sum(1 for g in self._goals if g["status"] == GoalStatus.COMPLETED.value)
        em_andamento = sum(1 for g in self._goals if g["status"] == GoalStatus.IN_PROGRESS.value)
        pendentes = sum(1 for g in self._goals if g["status"] == GoalStatus.PENDING.value)
        
        media_progresso = 0.0
        if self._goals:
            media_progresso = sum(g["progresso"] for g in self._goals) / total
        
        return {
            "total": total,
            "concluidos": concluidos,
            "em_andamento": em_andamento,
            "pendentes": pendentes,
            "media_progresso": round(media_progresso, 2),
            "label_progresso": self.get_scoring_label(media_progresso)
        }
    
    def get_proximas_acoes(self) -> List[Dict]:
        acoes = []
        
        for goal in self._goals:
            if goal["status"] == GoalStatus.IN_PROGRESS.value:
                for kr in goal["resultados_chave"]:
                    if kr["atual"] < kr["meta"]:
                        acoes.append({
                            "objetivo": goal["titulo"],
                            "resultado_chave": kr["titulo"],
                            "progresso": f"{kr['atual']}/{kr['meta']}",
                            "prioridade": goal["prioridade"]
                        })
        
        acoes.sort(key=lambda x: x["prioridade"], reverse=True)
        return acoes[:5]


_goals_instance = None

def get_goal_pursuit(data_dir: str = None) -> GoalPursuit:
    global _goals_instance
    if _goals_instance is None:
        _goals_instance = GoalPursuit(data_dir)
    return _goals_instance
