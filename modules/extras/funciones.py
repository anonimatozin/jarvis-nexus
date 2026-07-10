"""
JARVIS Extra Functions v1.0 - Funcionalidades adicionais.
"""
import os
import sys
import json
import time
import math
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import threading

class TimerManager:
    """Gerencia timers e alarmes."""
    
    def __init__(self):
        self._timers = {}
        self._counter = 0
    
    def criar_timer(self, segundos, mensagem="Timer finalizado"):
        """Cria um timer countdown."""
        self._counter += 1
        timer_id = self._counter
        
        def _executar():
            time.sleep(segundos)
            if timer_id in self._timers:
                del self._timers[timer_id]
                return True, mensagem
            return False, "Timer cancelado"
        
        t = threading.Thread(target=_executar, daemon=True)
        self._timers[timer_id] = {"thread": t, "inicio": time.time(), "duracao": segundos, "mensagem": mensagem}
        t.start()
        return timer_id
    
    def cancelar_timer(self, timer_id):
        """Cancela um timer."""
        if timer_id in self._timers:
            del self._timers[timer_id]
            return True
        return False
    
    def listar_timers(self):
        """Lista timers ativos."""
        resultado = []
        for tid, info in self._timers.items():
            elapsed = time.time() - info["inicio"]
            restante = max(0, info["duracao"] - elapsed)
            resultado.append({"id": tid, "restante_seg": int(restante), "mensagem": info["mensagem"]})
        return resultado


class Calculadora:
    """Calculadora segura com expressoes matematicas."""
    
    OPERACOES = {
        "soma": "+", "mais": "+", "somar": "+", "adicionar": "+",
        "subtracao": "-", "menos": "-", "subtrair": "-", "diminuir": "-",
        "multiplicacao": "*", "vezes": "*", "multiplicar": "*", "por": "*",
        "divisao": "/", "dividir": "/", "raiz": "sqrt",
        "potencia": "**", "elevado": "**", "quadrado": "**2", "cubo": "**3",
        "pi": "math.pi", "e": "math.e",
        "seno": "math.sin", "cosseno": "math.cos", "tangente": "math.tan",
        "logaritmo": "math.log10", "log": "math.log", "ln": "math.log",
        "absoluto": "abs", "valor_absoluto": "abs",
    }
    
    def calcular(self, expressao):
        """Calcula uma expressao matematica de forma segura."""
        try:
            expr = expressao.lower().strip()
            
            # Substitui palavras por operadores
            for palavra, operador in self.OPERACOES.items():
                expr = expr.replace(palavra, operador)
            
            # Remove caracteres perigosos
            permitidos = set("0123456789+-*/.() sqrtabcefilogmpow ")
            if not all(c in permitidos for c in expr):
                return "Expressao invalida."
            
            # Avalia
            resultado = eval(expr, {"__builtins__": {}, "math": math})
            return f"Resultado: {resultado}"
        except Exception as e:
            return f"Erro ao calcular: {e}"


class LembreteManager:
    """Gerencia lembretes."""
    
    def __init__(self):
        self._lembretes = []
        self._data_file = Path(__file__).parent.parent.parent / "data" / "lembretes.json"
        self._carregar()
    
    def _carregar(self):
        """Carrega lembretes do disco."""
        try:
            if self._data_file.exists():
                with open(self._data_file, "r", encoding="utf-8") as f:
                    self._lembretes = json.load(f)
        except:
            self._lembretes = []
    
    def _salvar(self):
        """Salva lembretes no disco."""
        try:
            self._data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._data_file, "w", encoding="utf-8") as f:
                json.dump(self._lembretes, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def adicionar(self, texto, horas=None, minutos=None, data=None):
        """Adiciona um lembrete."""
        lembrete = {
            "id": len(self._lembretes) + 1,
            "texto": texto,
            "horas": horas,
            "minutos": minutos,
            "data": data,
            "criado": datetime.now().isoformat(),
            "ativo": True
        }
        self._lembretes.append(lembrete)
        self._salvar()
        return lembrete["id"]
    
    def listar(self):
        """Lista lembretes ativos."""
        return [l for l in self._lembretes if l.get("ativo", True)]
    
    def remover(self, lembrete_id):
        """Remove um lembrete."""
        for l in self._lembretes:
            if l["id"] == lembrete_id:
                l["ativo"] = False
                self._salvar()
                return True
        return False


class SistemaInfo:
    """Informacoes do sistema."""
    
    @staticmethod
    def info_completa():
        """Retorna informacoes completas do sistema."""
        import platform
        import psutil
        
        info = {
            "sistema": platform.system(),
            "versao": platform.version(),
            "arquitetura": platform.architecture()[0],
            "processador": platform.processor(),
            "nome_maquina": platform.node(),
            "python": platform.python_version(),
        }
        
        try:
            info["cpu_percent"] = psutil.cpu_percent(interval=1)
            info["ram_total_gb"] = round(psutil.virtual_memory().total / (1024**3), 1)
            info["ram_usada_percent"] = psutil.virtual_memory().percent
            info["disco_total_gb"] = round(psutil.disk_usage('/').total / (1024**3), 1)
            info["disco_usado_percent"] = psutil.disk_usage('/').percent
        except:
            pass
        
        return info
    
    @staticmethod
    def info_formatada():
        """Retorna informacoes formatadas para fala."""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            disco = psutil.disk_usage('/').percent
            
            return f"CPU em {int(cpu)} por cento, memoria em {int(ram)} por cento, disco em {int(disco)} por cento."
        except:
            return "Nao foi possivel obter informacoes do sistema."


class MonitorProcessos:
    """Monitora processos do sistema."""
    
    @staticmethod
    def top_processos(n=5):
        """Retorna os N processos que mais usam CPU."""
        import psutil
        processos = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] and info['cpu_percent'] > 0:
                    processos.append({
                        "pid": info['pid'],
                        "nome": info['name'],
                        "cpu": round(info['cpu_percent'], 1),
                        "ram": round(info['memory_percent'], 1)
                    })
            except:
                pass
        
        processos.sort(key=lambda x: x['cpu'], reverse=True)
        return processos[:n]
    
    @staticmethod
    def formatar_top(n=5):
        """Formato para fala."""
        tops = MonitorProcessos.top_processos(n)
        if not tops:
            return "Nenhum processo significativo encontrado."
        
        partes = []
        for i, p in enumerate(tops, 1):
            partes.append(f"{p['nome']} com {p['cpu']} por cento de CPU")
        
        return "Top processos: " + ", ".join(partes) + "."


# Instancias globais
_timer_manager = None
_calculadora = None
_lembretes = None

def get_timer_manager():
    global _timer_manager
    if _timer_manager is None:
        _timer_manager = TimerManager()
    return _timer_manager

def get_calculadora():
    global _calculadora
    if _calculadora is None:
        _calculadora = Calculadora()
    return _calculadora

def get_lembretes():
    global _lembretes
    if _lembretes is None:
        _lembretes = LembreteManager()
    return _lembretes
