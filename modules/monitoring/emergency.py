# modules/monitoring/emergency.py
"""
J.A.R.V.I.S. - Emergency Response System
Monitoramento critico do sistema com resposta automatica.
Inspirado no imranshiundu/Jarvis.
"""

import psutil
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
import json

class EmergencyResponse:
    """Sistema de resposta a emergencias do sistema."""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.config = {
            'cpu_critical': 95,
            'cpu_warning': 85,
            'ram_critical': 95,
            'ram_warning': 85,
            'disk_critical': 5,  # GB livres
            'disk_warning': 10,
            'temp_critical': 90,  # Celsius
        }
        
        self.history = []
        self.alerts_cooldown = {}
        self.monitoring = False
        
        self.config_file = Path(__file__).parent.parent.parent / "data" / "emergency_config.json"
        self._load_config()
    
    def _load_config(self):
        """Carrega configuracao."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config.update(json.load(f))
        except Exception:
            pass
    
    def _save_config(self):
        """Salva configuracao."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass
    
    def get_system_state(self):
        """Retorna estado atual do sistema."""
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Tenta obter temperatura
        temp = None
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            temp = entries[0].current
                            break
        except Exception:
            pass
        
        # Bateria (se notebook)
        battery = None
        try:
            bat = psutil.sensors_battery()
            if bat:
                battery = {
                    'percent': bat.percent,
                    'plugged': bat.power_plugged
                }
        except Exception:
            pass
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu,
            'ram_percent': ram.percent,
            'ram_used_gb': round(ram.used / (1024**3), 1),
            'ram_total_gb': round(ram.total / (1024**3), 1),
            'disk_percent': disk.percent,
            'disk_free_gb': round(disk.free / (1024**3), 1),
            'disk_total_gb': round(disk.total / (1024**3), 1),
            'temperature': temp,
            'battery': battery,
        }
    
    def check_emergencies(self, state=None):
        """Verifica e retorna emergencias ativas."""
        if state is None:
            state = self.get_system_state()
        
        emergencies = []
        now = datetime.now()
        
        # CPU critica
        if state['cpu_percent'] >= self.config['cpu_critical']:
            if self._can_alert('cpu_critical', now, 30):
                emergencies.append({
                    'level': 'critical',
                    'type': 'cpu',
                    'message': f"CPU CRITICA: {state['cpu_percent']}%",
                    'recommendations': [
                        "Fechar processos pesados (Task Manager)",
                        "Reduzir prioridade de processos",
                        "Verificar processos suspicious"
                    ]
                })
        elif state['cpu_percent'] >= self.config['cpu_warning']:
            if self._can_alert('cpu_warning', now, 60):
                emergencies.append({
                    'level': 'warning',
                    'type': 'cpu',
                    'message': f"CPU alta: {state['cpu_percent']}%",
                    'recommendations': [
                        "Monitorar processos",
                        "Fechar apps desnecessarios"
                    ]
                })
        
        # RAM critica
        if state['ram_percent'] >= self.config['ram_critical']:
            if self._can_alert('ram_critical', now, 30):
                emergencies.append({
                    'level': 'critical',
                    'type': 'ram',
                    'message': f"RAM CRITICA: {state['ram_percent']}% ({state['ram_used_gb']}GB/{state['ram_total_gb']}GB)",
                    'recommendations': [
                        "Fechar navegador e apps pesados",
                        "Limpar cache",
                        "Reiniciar servicos"
                    ]
                })
        elif state['ram_percent'] >= self.config['ram_warning']:
            if self._can_alert('ram_warning', now, 60):
                emergencies.append({
                    'level': 'warning',
                    'type': 'ram',
                    'message': f"RAM alta: {state['ram_percent']}%",
                    'recommendations': [
                        "Fechar abas do navegador",
                        "Fechar apps em background"
                    ]
                })
        
        # Disco critico
        if state['disk_free_gb'] <= self.config['disk_critical']:
            if self._can_alert('disk_critical', now, 300):
                emergencies.append({
                    'level': 'critical',
                    'type': 'disk',
                    'message': f"POUCO ESPACO: {state['disk_free_gb']}GB livres",
                    'recommendations': [
                        "Limpar arquivos temporarios (temp)",
                        "Esvaziar lixeira",
                        "Desinstalar programas grandes",
                        "Mover arquivos para pendrive/cloud"
                    ]
                })
        elif state['disk_free_gb'] <= self.config['disk_warning']:
            if self._can_alert('disk_warning', now, 600):
                emergencies.append({
                    'level': 'warning',
                    'type': 'disk',
                    'message': f"Espaco baixo: {state['disk_free_gb']}GB livres",
                    'recommendations': [
                        "Limpar downloads antigos",
                        "Limpar cache do navegador"
                    ]
                })
        
        # Temperatura
        if state.get('temperature') and state['temperature'] >= self.config['temp_critical']:
            if self._can_alert('temp', now, 60):
                emergencies.append({
                    'level': 'critical',
                    'type': 'temperature',
                    'message': f"TEMPERATURA ALTA: {state['temperature']}°C",
                    'recommendations': [
                        "Verificar ventilacao",
                        "Reduzir carga de processamento",
                        "Verificar pasta termica"
                    ]
                })
        
        # Salva no historico
        for emerg in emergencies:
            self.history.append({
                **emerg,
                'timestamp': now.isoformat()
            })
        
        return emergencies
    
    def _can_alert(self, alert_type, now, cooldown_minutes):
        """Verifica se pode enviar alerta."""
        last = self.alerts_cooldown.get(alert_type)
        if last and (now - last) < timedelta(minutes=cooldown_minutes):
            return False
        self.alerts_cooldown[alert_type] = now
        return True
    
    def get_health_report(self):
        """Retorna relatorio completo de saude do sistema."""
        state = self.get_system_state()
        emergencies = self.check_emergencies(state)
        
        report = {
            'status': 'OK' if not emergencies else 'ALERTA',
            'timestamp': state['timestamp'],
            'system': state,
            'emergencies': emergencies,
            'uptime': self._get_uptime(),
        }
        
        return report
    
    def _get_uptime(self):
        """Retorna tempo ligado."""
        try:
            boot = datetime.fromtimestamp(psutil.boot_time())
            delta = datetime.now() - boot
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            return f"{days}d {hours}h {minutes}m"
        except Exception:
            return "Desconhecido"
    
    def start_monitoring(self, interval=60):
        """Inicia monitoramento em background."""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor():
            while self.monitoring:
                try:
                    emergencies = self.check_emergencies()
                    if emergencies and self.callback:
                        self.callback(emergencies)
                except Exception as e:
                    print(f"[EMERGENCY] Erro: {e}")
                time.sleep(interval)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        """Para o monitoramento."""
        self.monitoring = False
    
    def auto_cleanup(self):
        """Limpeza automatica do sistema."""
        actions_taken = []
        
        try:
            # Limpa temp
            import tempfile
            import os
            temp_dir = tempfile.gettempdir()
            files_before = len(os.listdir(temp_dir))
            
            for file in os.listdir(temp_dir):
                try:
                    filepath = os.path.join(temp_dir, file)
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                except Exception:
                    pass
            
            files_after = len(os.listdir(temp_dir))
            actions_taken.append(f"Temp limpo: {files_before - files_after} arquivos removidos")
        except Exception as e:
            actions_taken.append(f"Erro ao limpar temp: {e}")
        
        # Limpa cache do pip
        try:
            import subprocess
            subprocess.run(['pip', 'cache', 'purge'], capture_output=True)
            actions_taken.append("Cache do pip limpo")
        except Exception:
            pass
        
        return actions_taken
    
    def kill_heavy_processes(self, threshold_percent=50):
        """Mata processos que usam muita CPU."""
        killed = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if proc.info['cpu_percent'] > threshold_percent:
                    proc.kill()
                    killed.append(proc.info['name'])
            except Exception:
                pass
        
        return killed


def criar_modulo_emergency(callback=None):
    """Retorna instancia do modulo de emergencia."""
    return EmergencyResponse(callback=callback)
