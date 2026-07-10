"""
Proactive Autonomy Engine
Inspirado no sutando/JarvisAI - age sozinho quando ocioso.
"""
import time
import threading
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum


class AutonomyLevel(Enum):
    OFF = 0          # So responde quando chamado
    MAINTENANCE = 1  # Bots rodam agendados
    PROACTIVE = 2    # Sugere acoes quando ocioso
    FULL_AUTO = 3    # Persegue objetivos sozinho


class ProactiveEngine:
    """
    Motor de autonomia proativa.
    Monitora inatividade e executa acoes quando o usuario nao esta usando.
    """
    
    def __init__(self, level: AutonomyLevel = AutonomyLevel.MAINTENANCE):
        self.level = level
        self._idle_threshold = 300  # 5 minutos
        self._last_activity = time.time()
        self._running = False
        self._thread = None
        
        self._actions = []
        self._goals = []
        self._completed_goals = []
        
        self._config_file = Path("data/autonomy_config.json")
        self._load_config()
        
        print(f"[AUTONOMY] Nivel: {self.level.name}")
    
    def _load_config(self):
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.level = AutonomyLevel(config.get("level", 1))
                    self._idle_threshold = config.get("idle_threshold", 300)
                    self._goals = config.get("goals", [])
            except Exception:
                pass
    
    def _save_config(self):
        try:
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump({
                    "level": self.level.value,
                    "idle_threshold": self._idle_threshold,
                    "goals": self._goals
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AUTONOMY] Erro salvar config: {e}")
    
    def set_level(self, level: AutonomyLevel):
        self.level = level
        self._save_config()
        print(f"[AUTONOMY] Nivel alterado para: {level.name}")
    
    def registrar_atividade(self):
        self._last_activity = time.time()
    
    def registrar_acao(self, acao: Dict):
        self._actions.append({
            "timestamp": datetime.now().isoformat(),
            **acao
        })
    
    def adicionar_objetivo(self, objetivo: str, prioridade: int = 5, 
                          contexto: str = "") -> Dict:
        goal = {
            "id": len(self._goals) + 1,
            "objetivo": objetivo,
            "prioridade": prioridade,
            "contexto": contexto,
            "criado_em": datetime.now().isoformat(),
            "status": "pendente"
        }
        self._goals.append(goal)
        self._save_config()
        return goal
    
    def listar_objetivos(self) -> List[Dict]:
        return [g for g in self._goals if g["status"] == "pendente"]
    
    def concluir_objetivo(self, goal_id: int, resultado: str = ""):
        for goal in self._goals:
            if goal["id"] == goal_id:
                goal["status"] = "concluido"
                goal["concluido_em"] = datetime.now().isoformat()
                goal["resultado"] = resultado
                self._completed_goals.append(goal)
                self._goals.remove(goal)
                self._save_config()
                return True
        return False
    
    def _get_tempo_inatividade(self) -> float:
        return time.time() - self._last_activity
    
    def _verificar_acoes_proativas(self) -> List[str]:
        sugestoes = []
        
        inactivity = self._get_tempo_inatividade()
        
        if self.level.value >= AutonomyLevel.PROACTIVE.value:
            if inactivity > self._idle_threshold:
                sugestoes.append("Sistema ocioso ha mais de 5 minutos")
                
                if len(self._goals) > 0:
                    sugestoes.append(f"Ha {len(self._goals)} objetivos pendentes")
        
        return sugestoes
    
    def executar_manutencao(self) -> Dict:
        resultado = {
            "timestamp": datetime.now().isoformat(),
            "tipo": "manutencao",
            "acoes": []
        }
        
        # Verifica espaco em disco
        import psutil
        disco = psutil.disk_usage("C:\\")
        if disco.percent > 90:
            resultado["acoes"].append(f"Disco cheio: {disco.percent}%")
        
        # Verifica memoria
        ram = psutil.virtual_memory()
        if ram.percent > 85:
            resultado["acoes"].append(f"RAM alta: {ram.percent}%")
        
        # Verifica CPU
        cpu = psutil.cpu_percent(interval=1)
        if cpu > 90:
            resultado["acoes"].append(f"CPU alta: {cpu}%")
        
        print(f"[AUTONOMY] Manutencao: {len(resultado['acoes'])} alertas")
        return resultado
    
    def iniciar(self):
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[AUTONOMY] Loop proativo iniciado")
    
    def parar(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[AUTONOMY] Loop proativo parado")
    
    def _loop(self):
        while self._running:
            try:
                if self.level.value >= AutonomyLevel.MAINTENANCE.value:
                    inactivity = self._get_tempo_inatividade()
                    
                    if inactivity > self._idle_threshold * 2:
                        self.executar_manutencao()
                
                if self.level.value >= AutonomyLevel.FULL_AUTO.value:
                    sugestoes = self._verificar_acoes_proativas()
                    if sugestoes:
                        print(f"[AUTONOMY] Sugestoes: {sugestoes}")
                
                time.sleep(60)
            except Exception as e:
                print(f"[AUTONOMY] Erro no loop: {e}")
                time.sleep(60)
    
    def get_status(self) -> Dict:
        return {
            "nivel": self.level.name,
            "nivel_valor": self.level.value,
            "tempo_inatividade": int(self._get_tempo_inatividade()),
            "objetivos_pendentes": len(self._goals),
            "objetivos_concluidos": len(self._completed_goals),
            "total_acoes": len(self._actions),
            "rodando": self._running
        }


_engine_instance = None

def get_proactive_engine(level: AutonomyLevel = None) -> ProactiveEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ProactiveEngine(level or AutonomyLevel.MAINTENANCE)
    return _engine_instance
