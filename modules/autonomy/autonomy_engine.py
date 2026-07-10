# modules/autonomy/autonomy_engine.py
"""
J.A.R.V.I.S. - Autonomy Engine Module
Motor autonomo com self-learning avancado, aprende padroes temporais,
sequenciais e contextuais do usuario.
Inspirado no imranshiundu/Jarvis.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import threading

class AutonomyEngine:
    """Motor autonomo com aprendizado de padroes do usuario."""
    
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.patterns_file = self.data_dir / "user_patterns.json"
        self.routines_file = self.data_dir / "user_routines.json"
        self.emergency_file = self.data_dir / "emergency_config.json"
        
        self.patterns = self._load_json(self.patterns_file, {
            'temporal': {},    # Padroes por hora/dia
            'sequential': [],  # Sequencias de acoes
            'contextual': {},  # Padroes por contexto
            'frequency': {},   # Frequencia de comandos
        })
        
        self.routines = self._load_json(self.routines_file, {
            'daily': [],       # Rotinas diárias
            'weekly': [],      # Rotinas semanais
            'triggers': [],    # Gatilhos automaticos
        })
        
        self.emergency_config = self._load_json(self.emergency_file, {
            'max_cpu_percent': 90,
            'max_ram_percent': 85,
            'min_disk_free_gb': 5,
            'max_gpu_temp': 85,
            'alert_cooldown_minutes': 30,
        })
        
        self._command_history = []
        self._last_alerts = {}
        self._monitoring = False
    
    def _load_json(self, filepath, default):
        """Carrega arquivo JSON ou retorna default."""
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return default
    
    def _save_json(self, filepath, data):
        """Salva dados em JSON."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AUTONOMY] Erro ao salvar: {e}")
    
    # ═══ APRENDIZADO DE PADROES ═══
    
    def register_command(self, command, context=None):
        """Registra um comando para aprendizado."""
        now = datetime.now()
        
        # Padrao temporal (hora do dia)
        hour = now.hour
        hour_key = f"{hour:02d}:00"
        if hour_key not in self.patterns['temporal']:
            self.patterns['temporal'][hour_key] = {}
        if command not in self.patterns['temporal'][hour_key]:
            self.patterns['temporal'][hour_key][command] = 0
        self.patterns['temporal'][hour_key][command] += 1
        
        # Sequencia de acoes
        self.patterns['sequential'].append({
            'command': command,
            'time': now.isoformat(),
            'context': context
        })
        # Mantem apenas ultimas 100 acoes
        if len(self.patterns['sequential']) > 100:
            self.patterns['sequential'] = self.patterns['sequential'][-100:]
        
        # Frequencia total
        if command not in self.patterns['frequency']:
            self.patterns['frequency'][command] = 0
        self.patterns['frequency'][command] += 1
        
        # Contexto
        if context:
            if context not in self.patterns['contextual']:
                self.patterns['contextual'][context] = {}
            if command not in self.patterns['contextual'][context]:
                self.patterns['contextual'][context][command] = 0
            self.patterns['contextual'][context][command] += 1
        
        # Salva periodicamente
        if len(self._command_history) % 10 == 0:
            self._save_json(self.patterns_file, self.patterns)
        
        self._command_history.append(command)
    
    def predict_next_command(self, current_context=None):
        """Prediz qual comando o usuario provavelmente quer."""
        now = datetime.now()
        hour_key = f"{now.hour:02d}:00"
        
        candidates = {}
        
        # Padroes temporais
        if hour_key in self.patterns['temporal']:
            for cmd, count in self.patterns['temporal'][hour_key].items():
                candidates[cmd] = candidates.get(cmd, 0) + count * 2
        
        # Padroes de contexto
        if current_context and current_context in self.patterns['contextual']:
            for cmd, count in self.patterns['contextual'][current_context].items():
                candidates[cmd] = candidates.get(cmd, 0) + count * 3
        
        # Sequencia (ultimo comando costuma ser seguido de...)
        if self.patterns['sequential']:
            last_cmd = self.patterns['sequential'][-1]['command']
            for i, entry in enumerate(self.patterns['sequential'][-10:]):
                if i > 0 and self.patterns['sequential'][i-1]['command'] == last_cmd:
                    candidates[entry['command']] = candidates.get(entry['command'], 0) + 1
        
        # Frequencia geral
        for cmd, count in self.patterns['frequency'].items():
            candidates[cmd] = candidates.get(cmd, 0) + count * 0.5
        
        if not candidates:
            return None
        
        # Retorna o mais provavel
        return max(candidates, key=candidates.get)
    
    def get_common_commands(self, limit=10):
        """Retorna os comandos mais usados."""
        sorted_cmds = sorted(
            self.patterns['frequency'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_cmds[:limit]
    
    def get_time_recommendations(self):
        """Retorna recomendacoes baseadas na hora atual."""
        now = datetime.now()
        hour_key = f"{now.hour:02d}:00"
        
        if hour_key in self.patterns['temporal']:
            cmds = self.patterns['temporal'][hour_key]
            if cmds:
                top = sorted(cmds.items(), key=lambda x: x[1], reverse=True)[:3]
                return [f"{cmd} (usado {count}x)" for cmd, count in top]
        
        return ["Nenhuma recomendacao disponivel ainda."]
    
    # ═══ ROTINAS AUTOMATICAS ═══
    
    def add_daily_routine(self, time_str, command, days=None):
        """Adiciona uma rotina diaria."""
        routine = {
            'time': time_str,
            'command': command,
            'days': days or ['mon', 'tue', 'wed', 'thu', 'fri'],
            'enabled': True,
            'last_run': None
        }
        self.routines['daily'].append(routine)
        self._save_json(self.routines_file, self.routines)
        return f"Rotina adicionada: {command} as {time_str}"
    
    def add_trigger(self, condition, action):
        """Adiciona um gatilho automatico."""
        trigger = {
            'condition': condition,
            'action': action,
            'enabled': True
        }
        self.routines['triggers'].append(trigger)
        self._save_json(self.routines_file, self.routines)
        return f"Gatilho adicionado: quando {condition}, executar {action}"
    
    def check_triggers(self, system_state):
        """Verifica se algum gatilho deve ser acionado."""
        actions = []
        for trigger in self.routines['triggers']:
            if not trigger['enabled']:
                continue
            
            condition = trigger['condition']
            if self._evaluate_condition(condition, system_state):
                actions.append(trigger['action'])
        
        return actions
    
    def _evaluate_condition(self, condition, state):
        """Avalia uma condicao."""
        try:
            if 'cpu >' in condition:
                threshold = int(condition.split('>')[-1].strip())
                return state.get('cpu_percent', 0) > threshold
            elif 'ram >' in condition:
                threshold = int(condition.split('>')[-1].strip())
                return state.get('ram_percent', 0) > threshold
            elif 'disk <' in condition:
                threshold = int(condition.split('<')[-1].strip())
                return state.get('disk_free_gb', 100) < threshold
            elif 'time ==' in condition:
                target_time = condition.split('==')[-1].strip()
                return datetime.now().strftime('%H:%M') == target_time
        except Exception:
            pass
        return False
    
    # ═══ MONITORAMENTO DE EMERGENCIA ═══
    
    def start_monitoring(self, callback=None):
        """Inicia monitoramento do sistema em background."""
        if self._monitoring:
            return
        
        self._monitoring = True
        
        def monitor_loop():
            import psutil
            while self._monitoring:
                try:
                    cpu = psutil.cpu_percent(interval=1)
                    ram = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    
                    state = {
                        'cpu_percent': cpu,
                        'ram_percent': ram.percent,
                        'disk_free_gb': round(disk.free / (1024**3), 1),
                    }
                    
                    # Verifica emergencias
                    alerts = self.check_emergency(state)
                    
                    # Verifica gatilhos
                    trigger_actions = self.check_triggers(state)
                    
                    if (alerts or trigger_actions) and callback:
                        callback(alerts, trigger_actions)
                    
                except Exception as e:
                    print(f"[MONITOR] Erro: {e}")
                
                time.sleep(60)  # Verifica a cada minuto
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        """Para o monitoramento."""
        self._monitoring = False
    
    def check_emergency(self, state):
        """Verifica situacoes de emergencia."""
        alerts = []
        now = datetime.now()
        
        # CPU alta
        if state.get('cpu_percent', 0) > self.emergency_config['max_cpu_percent']:
            if self._can_alert('cpu', now):
                alerts.append({
                    'type': 'warning',
                    'message': f"CPU alta: {state['cpu_percent']}%",
                    'action': 'suggestion'
                })
        
        # RAM alta
        if state.get('ram_percent', 0) > self.emergency_config['max_ram_percent']:
            if self._can_alert('ram', now):
                alerts.append({
                    'type': 'warning',
                    'message': f"RAM alta: {state['ram_percent']}%",
                    'action': 'suggestion'
                })
        
        # Pouco espaco em disco
        if state.get('disk_free_gb', 100) < self.emergency_config['min_disk_free_gb']:
            if self._can_alert('disk', now):
                alerts.append({
                    'type': 'critical',
                    'message': f"Pouco espaco em disco: {state['disk_free_gb']}GB livres",
                    'action': 'cleanup'
                })
        
        return alerts
    
    def _can_alert(self, alert_type, now):
        """Verifica se pode enviar alerta (cooldown)."""
        cooldown = timedelta(minutes=self.emergency_config['alert_cooldown_minutes'])
        last = self._last_alerts.get(alert_type)
        
        if last is None or (now - last) > cooldown:
            self._last_alerts[alert_type] = now
            return True
        return False
    
    def get_emergency_actions(self, alert_type):
        """Retorna acoes recomendadas para emergencia."""
        actions = {
            'cpu': [
                "Fechar processos pesados",
                "Reduzir prioridade de processos",
                "Reiniciar servicos desnecessarios"
            ],
            'ram': [
                "Fechar aplicativos nao usados",
                "Limpar cache do sistema",
                "Reiniciar navegador"
            ],
            'disk': [
                "Limpar arquivos temporarios",
                "Esvaziar lixeira",
                "Desinstalar programas nao usados",
                "Mover arquivos para pendrive"
            ]
        }
        return actions.get(alert_type, [])
    
    # ═══ SUGESTOES INTELIGENTES ═══
    
    def get_smart_suggestions(self):
        """Gera sugestoes baseadas em padroes aprendidos."""
        suggestions = []
        
        # Comandos frequentes nesta hora
        time_recs = self.get_time_recommendations()
        if time_recs and time_recs[0] != "Nenhuma recomendacao disponivel ainda.":
            suggestions.append(f"Nesta hora voce costuma: {time_recs[0]}")
        
        # Comandos mais usados
        common = self.get_common_commands(3)
        if common:
            cmds = ", ".join([f"{cmd}" for cmd, _ in common])
            suggestions.append(f"Seus comandos favoritos: {cmds}")
        
        # Rotinas pendentes
        if self.routines['daily']:
            now = datetime.now()
            for routine in self.routines['daily']:
                if routine['enabled'] and routine['time'] == now.strftime('%H:%M'):
                    suggestions.append(f"Hora de executar: {routine['command']}")
        
        return suggestions


def criar_modulo_autonomy():
    """Retorna instancia do modulo de autonomia."""
    return AutonomyEngine()
