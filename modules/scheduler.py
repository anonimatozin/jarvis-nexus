"""
NEXUS - Scheduler & Monitor Proativo v1.0
═══════════════════════════════════════════════════════════
Tarefas agendadas + monitoramento em background.
Roda em thread separada, sem bloquear o jarvis.
═══════════════════════════════════════════════════════════
"""

import os
import re
import time
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional


# ════════════════════════════════════════════════════════════
# AGENDA - Tarefas planejadas
# ════════════════════════════════════════════════════════════

class Agenda:
    """Gerencia tarefas agendadas (cron-like)."""
    
    def __init__(self, persist_file="data/agenda.json"):
        self.persist_file = persist_file
        self.tarefas = []  # lista de dicts
        self._load()
    
    def _load(self):
        try:
            if os.path.exists(self.persist_file):
                with open(self.persist_file, "r", encoding="utf-8") as f:
                    self.tarefas = json.load(f)
        except Exception as e:
            print(f"[AGENDA] erro load: {e}")
            self.tarefas = []
    
    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.persist_file), exist_ok=True)
            with open(self.persist_file, "w", encoding="utf-8") as f:
                json.dump(self.tarefas, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AGENDA] erro save: {e}")
    
    def adicionar(self, tipo, quando, mensagem, dados=None):
        """
        Adiciona uma tarefa agendada.
        tipo: "once" (uma vez), "daily" (diaria), "interval" (intervalo)
        quando: "HH:MM" para once/daily, segundos para interval
        mensagem: o que falar quando disparar
        """
        tarefa = {
            "id": f"task_{int(time.time() * 1000)}",
            "tipo": tipo,
            "quando": quando,
            "mensagem": mensagem,
            "dados": dados or {},
            "criada_em": datetime.now().isoformat(),
            "ativa": True,
            "ultima_execucao": None,
        }
        
        # Para "interval", calcula proxima execucao
        if tipo == "interval":
            try:
                segundos = int(quando)
                tarefa["proxima"] = (datetime.now() + timedelta(seconds=segundos)).isoformat()
            except:
                return None
        elif tipo == "once":
            # quando = "HH:MM" ou "YYYY-MM-DD HH:MM"
            try:
                if " " in quando:
                    dt = datetime.strptime(quando, "%Y-%m-%d %H:%M")
                else:
                    # So hora, assume hoje
                    h, m = quando.split(":")
                    dt = datetime.now().replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                    if dt < datetime.now():
                        dt += timedelta(days=1)
                tarefa["proxima"] = dt.isoformat()
            except:
                return None
        elif tipo == "daily":
            # quando = "HH:MM" todo dia
            try:
                h, m = quando.split(":")
                dt = datetime.now().replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                if dt < datetime.now():
                    dt += timedelta(days=1)
                tarefa["proxima"] = dt.isoformat()
            except:
                return None
        
        self.tarefas.append(tarefa)
        self._save()
        return tarefa["id"]
    
    def remover(self, task_id):
        self.tarefas = [t for t in self.tarefas if t["id"] != task_id]
        self._save()
    
    def listar(self):
        return [t for t in self.tarefas if t.get("ativa")]
    
    def verificar(self):
        """Retorna lista de tarefas que devem disparar AGORA."""
        agora = datetime.now()
        disparar = []
        
        for t in self.tarefas:
            if not t.get("ativa"):
                continue
            
            try:
                proxima = datetime.fromisoformat(t.get("proxima", ""))
                if agora >= proxima:
                    disparar.append(t)
                    
                    # Atualiza proxima execucao
                    if t["tipo"] == "once":
                        t["ativa"] = False
                    elif t["tipo"] == "daily":
                        t["proxima"] = (proxima + timedelta(days=1)).isoformat()
                    elif t["tipo"] == "interval":
                        seg = int(t["quando"])
                        t["proxima"] = (agora + timedelta(seconds=seg)).isoformat()
                    
                    t["ultima_execucao"] = agora.isoformat()
            except Exception as e:
                print(f"[AGENDA] erro check {t.get('id')}: {e}")
        
        if disparar:
            self._save()
        
        return disparar
    
    def limpar_todas(self):
        self.tarefas = []
        self._save()


# ════════════════════════════════════════════════════════════
# MONITOR - Vigia sistema e dispara alertas
# ════════════════════════════════════════════════════════════

class Monitor:
    """Monitora sistema e dispara alertas proativos."""
    
    def __init__(self, system_control=None):
        self.system_control = system_control
        # Limites
        self.cpu_limite = 999
        self.ram_limite = 999
        self.disco_limite = 999
        self.bateria_limite = 20
        
        # Estado (evita alertar repetidamente)
        self._ultimo_alerta_cpu = 0
        self._ultimo_alerta_ram = 0
        self._ultimo_alerta_disco = 0
        self._ultimo_alerta_bateria = 0
        self._cooldown = 300  # 5 minutos entre alertas iguais
        
        # Contador de CPU alta (precisa ficar alta por X segundos)
        self._cpu_alta_desde = None
    
    def verificar(self):
        """Verifica sistema e retorna lista de alertas."""
        alertas = []
        agora = time.time()
        
        if not self.system_control:
            return alertas
        
        try:
            info = self.system_control.get_system_info()
        except Exception:
            return alertas
        
        cpu = info.get("cpu_percent", 0)
        ram = info.get("ram_used_percent", 0)
        disco = info.get("disk_used_percent", 0)
        
        # CPU alta sustentada
        if cpu > self.cpu_limite:
            if self._cpu_alta_desde is None:
                self._cpu_alta_desde = agora
            elif agora - self._cpu_alta_desde > 60:  # 1 min sustentado
                if agora - self._ultimo_alerta_cpu > self._cooldown:
                    alertas.append({
                        "tipo": "cpu_alta",
                        "mensagem": f"Sir, CPU em {int(cpu)} por cento ha mais de um minuto. Pode estar sobrecarregado.",
                        "valor": cpu,
                    })
                    self._ultimo_alerta_cpu = agora
                    self._cpu_alta_desde = None
        else:
            self._cpu_alta_desde = None
        
        # RAM alta
        if ram > self.ram_limite:
            if agora - self._ultimo_alerta_ram > self._cooldown:
                alertas.append({
                    "tipo": "ram_alta",
                    "mensagem": f"Memoria em {int(ram)} por cento, Sir. Considere fechar alguns programas.",
                    "valor": ram,
                })
                self._ultimo_alerta_ram = agora
        
        # Disco
        if disco > self.disco_limite:
            if agora - self._ultimo_alerta_disco > self._cooldown * 6:  # 30 min
                alertas.append({
                    "tipo": "disco_cheio",
                    "mensagem": f"Disco com {int(disco)} por cento de uso. Espaco critico, Sir.",
                    "valor": disco,
                })
                self._ultimo_alerta_disco = agora
        
        # Bateria baixa
        if "battery_percent" in info:
            bat = info["battery_percent"]
            plug = info.get("battery_plugged", True)
            if not plug and bat < self.bateria_limite:
                if agora - self._ultimo_alerta_bateria > self._cooldown * 2:
                    alertas.append({
                        "tipo": "bateria_baixa",
                        "mensagem": f"Bateria em {int(bat)} por cento, Sir. Considere conectar o carregador.",
                        "valor": bat,
                    })
                    self._ultimo_alerta_bateria = agora
        
        return alertas


# ════════════════════════════════════════════════════════════
# SCHEDULER - Orquestrador (roda em background)
# ════════════════════════════════════════════════════════════

class Scheduler:
    """
    Orquestrador: roda Agenda + Monitor em background.
    Dispara callback quando algo precisa ser falado/feito.
    """
    
    def __init__(self, callback_fala=None, system_control=None):
        """
        Args:
            callback_fala: funcao(texto) chamada quando dispara alerta/tarefa
            system_control: instancia de SystemControl para monitorar
        """
        self.agenda = Agenda()
        self.monitor = Monitor(system_control)
        self.callback_fala = callback_fala
        self.running = False
        self.thread = None
    
    def iniciar(self):
        """Inicia o loop de verificacao em background."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True, name="scheduler")
        self.thread.start()
        print("[SCHEDULER] Iniciado em background.")
    
    def parar(self):
        self.running = False
    
    def _loop(self):
        """Loop principal - verifica a cada 30 segundos."""
        while self.running:
            try:
                # Verifica agenda
                tarefas = self.agenda.verificar()
                for t in tarefas:
                    msg = t.get("mensagem", "Lembrete agendado.")

                    # Trata briefings especiais
                    if msg.startswith("[BRIEFING_"):
                        periodo = msg.replace("[BRIEFING_", "").replace("]", "").lower()
                        if hasattr(self, 'briefer') and self.briefer:
                            texto = self.briefer.gerar_briefing(periodo)
                            if texto:
                                self._disparar(texto)
                        continue

                    self._disparar(f"Lembrete, Sir. {msg}")
                
                # Verifica monitor
                alertas = self.monitor.verificar()
                for a in alertas:
                    self._disparar(a["mensagem"])
            except Exception as e:
                print(f"[SCHEDULER] erro: {e}")
            
            # Espera 30 segundos
            for _ in range(30):
                if not self.running:
                    break
                time.sleep(1)
    
    def _disparar(self, texto):
        """Dispara fala via callback."""
        if self.callback_fala:
            try:
                self.callback_fala(texto)
            except Exception as e:
                print(f"[SCHEDULER] erro callback: {e}")
    
    # ═══ API PUBLICA - Comandos do usuario ═══
    
    def agendar_lembrete(self, quando, mensagem):
        """Agenda lembrete. quando = 'HH:MM' ou 'em X minutos'."""
        # Parse "em X minutos"
        m = re.match(r'(?:em\s+|daqui\s+)(\d+)\s*(minuto|segundo|hora)', quando.lower())
        if m:
            num = int(m.group(1))
            unidade = m.group(2)
            if "segundo" in unidade:
                seg = num
            elif "minuto" in unidade:
                seg = num * 60
            elif "hora" in unidade:
                seg = num * 3600
            else:
                seg = num * 60
            
            # MUDADO: era "interval" (infinito), agora "once" (uma vez)
            # Converte segundos em datetime futuro
            from datetime import datetime, timedelta
            quando_dt = datetime.now() + timedelta(seconds=seg)
            quando_str = quando_dt.strftime("%Y-%m-%d %H:%M")
            return self.agenda.adicionar("once", quando_str, mensagem)
        
        # Parse "HH:MM"
        if re.match(r'\d{1,2}:\d{2}', quando):
            return self.agenda.adicionar("once", quando, mensagem)
        
        return None
    
    def agendar_diario(self, hora, mensagem):
        """Agenda lembrete diario. hora = 'HH:MM'."""
        return self.agenda.adicionar("daily", hora, mensagem)
    
    def listar_agendamentos(self):
        return self.agenda.listar()
    
    def cancelar_todos(self):
        self.agenda.limpar_todas()
        return True

    def agendar_unico(self, segundos, mensagem):
        """Agenda uma acao unica em X segundos."""
        from datetime import datetime, timedelta
        quando = datetime.now() + timedelta(seconds=segundos)
        quando_str = quando.strftime("%Y-%m-%d %H:%M")
        return self.agenda.adicionar("once", quando_str, mensagem)

    def listar(self):
        """Lista agendamentos (alias para listar_agendamentos)."""
        return self.listar_agendamentos()

    def pomodoro(self, duracao_min=25):
        """Inicia um timer pomodoro."""
        from datetime import datetime, timedelta
        agora = datetime.now()
        fim = agora + timedelta(minutes=duracao_min)
        fim_str = fim.strftime("%Y-%m-%d %H:%M")
        resultado = self.agenda.adicionar("once", fim_str, "Pomodoro finalizado! Hora de descansar.")
        if resultado:
            return f"Pomodoro iniciado! {duracao_min} minutos. Volta as {fim.strftime('%H:%M')}."
        return "Erro ao iniciar pomodoro."

    def listar_tarefas(self):
        """Lista tarefas agendadas."""
        return self.listar_agendamentos()


# ════════════════════════════════════════════════════════════
# BRIEFEF - Ciclo diario automatico
# ════════════════════════════════════════════════════════════

class Briefer:
    """
    Gera briefings diarios automaticos.
    Ciclo: manha (08:00), tarde (12:00), noite (18:00), resumo (22:00)
    """

    HORARIOS = {
        "manha": "08:00",
        "tarde": "12:00",
        "noite": "18:00",
        "resumo": "22:00",
    }

    def __init__(self, engine=None):
        self.engine = engine
        self._briefings_enviados = {}  # {data_tipo: True}

    def gerar_briefing(self, periodo):
        """Gera briefing para o periodo especificado."""
        from datetime import datetime
        agora = datetime.now()
        data_hoje = agora.strftime("%Y-%m-%d")
        chave = f"{data_hoje}_{periodo}"

        # Evita enviar briefing duplicado no mesmo dia
        if chave in self._briefings_enviados:
            return None

        partes = []

        if periodo == "manha":
            partes.append(f"Bom dia, Sir. Sao {agora.strftime('%H:%M')}.")
            partes.append("Este e o briefing matinal.")
            if self.engine:
                # Status do sistema
                try:
                    import psutil
                    cpu = psutil.cpu_percent(interval=0.5)
                    ram = psutil.virtual_memory().percent
                    partes.append(f"Sistema: CPU {int(cpu)}%, RAM {int(ram)}%.")
                except Exception:
                    pass
                # Pendrive
                try:
                    from modules.visual.pendrive import pendrive_conectado, get_espaco_livre_mb
                    if pendrive_conectado():
                        livre = get_espaco_livre_mb()
                        partes.append(f"Pendrive conectado: {livre}MB livres.")
                    else:
                        partes.append("Pendrive desconectado.")
                except Exception:
                    pass

        elif periodo == "tarde":
            partes.append(f"Sao {agora.strftime('%H:%M')}, Sir. Meio do dia.")
            if self.engine:
                try:
                    import psutil
                    cpu = psutil.cpu_percent(interval=0.5)
                    partes.append(f"CPU em {int(cpu)}%.")
                except Exception:
                    pass

        elif periodo == "noite":
            partes.append(f"Sao {agora.strftime('%H:%M')}, Sir. Fim do expediente.")
            if self.engine:
                try:
                    import psutil
                    ram = psutil.virtual_memory()
                    usado_gb = round(ram.used / (1024**3), 1)
                    total_gb = round(ram.total / (1024**3), 1)
                    partes.append(f"RAM: {usado_gb}GB de {total_gb}GB em uso.")
                except Exception:
                    pass

        elif periodo == "resumo":
            partes.append(f"Resumo do dia, Sir. Sao {agora.strftime('%H:%M')}.")
            # Conta tarefas do dia
            if self.engine and hasattr(self.engine, 'scheduler'):
                try:
                    tarefas = self.engine.scheduler.listar_agendamentos()
                    partes.append(f"{len(tarefas)} tarefas agendadas ativas.")
                except Exception:
                    pass

        self._briefings_enviados[chave] = True
        return " ".join(partes) if partes else None

    def registrar_no_scheduler(self, scheduler):
        """Registra briefings diarios no scheduler."""
        if not scheduler:
            return
        for periodo, hora in self.HORARIOS.items():
            scheduler.agendar_diario(hora, f"[BRIEFING_{periodo.upper()}]")
        print(f"[BRIEFING] {len(self.HORARIOS)} briefings diarios registrados")
