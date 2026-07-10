"""
JARVIS System Dashboard v1.0
Monitoramento avançado do sistema em tempo real.

Recursos:
  - CPU, RAM, Disco, Rede
  - Processos pesados
  - Temperatura (se disponível)
  - Gráficos de uso
  - Alertas automáticos
"""
import os
import psutil
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import threading


class SystemDashboard:
    """Dashboard de monitoramento do sistema."""

    def __init__(self):
        self._historico = {"cpu": [], "ram": [], "disco": [], "rede": []}
        self._max_historico = 100
        self._lock = threading.Lock()
        self._alertas = []
        self._limites = {
            "cpu_alta": 80,
            "ram_alta": 85,
            "disco_baixo": 10
        }

        print("[DASHBOARD] Inicializado")

    def obter_info_completa(self) -> Dict:
        """Obtém informações completas do sistema."""
        info = {
            "timestamp": datetime.now().isoformat(),
            "cpu": self.obter_cpu(),
            "ram": self.obter_ram(),
            "disco": self.obter_disco(),
            "rede": self.obter_rede(),
            "bateria": self.obter_bateria(),
            "processos": self.obter_top_processos(5)
        }

        # Atualiza histórico
        with self._lock:
            for key in ["cpu", "ram"]:
                if key in info:
                    self._historico[key].append(info[key]["percentual"])
                    if len(self._historico[key]) > self._max_historico:
                        self._historico[key].pop(0)

        # Verifica alertas
        self._verificar_alertas(info)

        return info

    def obter_cpu(self) -> Dict:
        """Informações da CPU."""
        try:
            freq = psutil.cpu_freq()
            return {
                "percentual": psutil.cpu_percent(interval=1),
                "nucleos": psutil.cpu_count(),
                "nucleos_fisicos": psutil.cpu_count(logical=False),
                "frequencia_mhz": round(freq.current, 2) if freq else 0,
                "temperatura": self._obter_temperatura_cpu()
            }
        except Exception:
            return {"percentual": 0, "erro": "Não disponível"}

    def obter_ram(self) -> Dict:
        """Informações da RAM."""
        try:
            mem = psutil.virtual_memory()
            return {
                "percentual": mem.percent,
                "total_gb": round(mem.total / (1024**3), 2),
                "disponivel_gb": round(mem.available / (1024**3), 2),
                "usada_gb": round(mem.used / (1024**3), 2)
            }
        except Exception:
            return {"percentual": 0, "erro": "Não disponível"}

    def obter_disco(self) -> Dict:
        """Informações do disco."""
        try:
            disk = psutil.disk_usage("/")
            return {
                "percentual": disk.percent,
                "total_gb": round(disk.total / (1024**3), 2),
                "usado_gb": round(disk.used / (1024**3), 2),
                "livre_gb": round(disk.free / (1024**3), 2)
            }
        except Exception:
            return {"percentual": 0, "erro": "Não disponível"}

    def obter_rede(self) -> Dict:
        """Informações de rede."""
        try:
            net = psutil.net_io_counters()
            return {
                "bytes_enviados": net.bytes_sent,
                "bytes_recebidos": net.bytes_recv,
                "enviados_mb": round(net.bytes_sent / (1024**2), 2),
                "recebidos_mb": round(net.bytes_recv / (1024**2), 2),
                "pacotes_enviados": net.packets_sent,
                "pacotes_recebidos": net.packets_recv
            }
        except Exception:
            return {"erro": "Não disponível"}

    def obter_bateria(self) -> Optional[Dict]:
        """Informações da bateria (laptop)."""
        try:
            bateria = psutil.sensors_battery()
            if bateria:
                return {
                    "percentual": bateria.percent,
                    "carregando": bateria.power_plugged,
                    "tempo_restante": bateria.secsleft if bateria.secsleft > 0 else None
                }
        except Exception:
            pass
        return None

    def _obter_temperatura_cpu(self) -> Optional[float]:
        """Tenta obter temperatura da CPU."""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        return entries[0].current
        except Exception:
            pass
        return None

    def obter_top_processos(self, top_n: int = 5) -> List[Dict]:
        """Lista processos mais pesados."""
        try:
            processos = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    if info['cpu_percent'] > 0 or info['memory_percent'] > 0:
                        processos.append({
                            "pid": info['pid'],
                            "nome": info['name'][:30],
                            "cpu": round(info['cpu_percent'], 1),
                            "ram_mb": round(info['memory_percent'] * psutil.virtual_memory().total / (1024**2), 1)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Ordena por CPU
            processos.sort(key=lambda x: x['cpu'], reverse=True)
            return processos[:top_n]
        except Exception:
            return []

    def _verificar_alertas(self, info: Dict):
        """Verifica e gera alertas."""
        cpu = info.get("cpu", {}).get("percentual", 0)
        ram = info.get("ram", {}).get("percentual", 0)
        disco = info.get("disco", {}).get("percentual", 0)

        if cpu > self._limites["cpu_alta"]:
            self._adicionar_alerta("CPU Alta", f"CPU em {cpu}%", "critico")
        if ram > self._limites["ram_alta"]:
            self._adicionar_alerta("RAM Alta", f"RAM em {ram}%", "critico")
        if (100 - disco) < self._limites["disco_baixo"]:
            self._adicionar_alerta("Disco Baixo", f"Disco livre: {100-disco}%", "aviso")

    def _adicionar_alerta(self, titulo: str, mensagem: str, nivel: str):
        """Adiciona alerta."""
        alerta = {
            "titulo": titulo,
            "mensagem": mensagem,
            "nivel": nivel,
            "timestamp": datetime.now().isoformat()
        }
        with self._lock:
            # Evita alertas duplicados recentes
            for a in self._alertas[-5:]:
                if a["titulo"] == titulo:
                    return
            self._alertas.append(alerta)
            if len(self._alertas) > 50:
                self._alertas.pop(0)

    def obter_alertas(self) -> List[Dict]:
        """Retorna alertas ativos."""
        with self._lock:
            return self._alertas.copy()

    def obter_historico(self, metrica: str = "cpu", ultimo: int = 30) -> List[float]:
        """Retorna histórico de uma métrica."""
        with self._lock:
            dados = self._historico.get(metrica, [])
        return dados[-ultimo:]

    def formatar_relatorio(self) -> str:
        """Gera relatório formatado do sistema."""
        info = self.obter_info_completa()

        relatorio = []
        relatorio.append("=" * 50)
        relatorio.append("  RELATÓRIO DO SISTEMA")
        relatorio.append("=" * 50)
        relatorio.append(f"  CPU:     {info['cpu']['percentual']}%")
        relatorio.append(f"  RAM:     {info['ram']['percentual']}% ({info['ram']['usada_gb']}GB / {info['ram']['total_gb']}GB)")
        relatorio.append(f"  Disco:   {info['disco']['percentual']}% ({info['disco']['livre_gb']}GB livre)")
        relatorio.append(f"  Rede:    ↓{info['rede']['recebidos_mb']}MB  ↑{info['rede']['enviados_mb']}MB")

        if info['bateria']:
            bat = info['bateria']
            relatorio.append(f"  Bateria: {bat['percentual']}% {'⚡' if bat['carregando'] else '🔋'}")

        relatorio.append("-" * 50)
        relatorio.append("  TOP PROCESSOS:")
        for proc in info['processos'][:3]:
            relatorio.append(f"    {proc['nome'][:20]:20s} CPU:{proc['cpu']:5.1f}% RAM:{proc['ram_mb']:6.1f}MB")

        if self._alertas:
            relatorio.append("-" * 50)
            relatorio.append("  ⚠️  ALERTAS:")
            for alerta in self._alertas[-3:]:
                relatorio.append(f"    [{alerta['nivel'].upper()}] {alerta['titulo']}: {alerta['mensagem']}")

        relatorio.append("=" * 50)
        return "\n".join(relatorio)

    def status(self) -> Dict:
        """Retorna status do dashboard."""
        return {
            "historico": {k: len(v) for k, v in self._historico.items()},
            "alertas": len(self._alertas),
            "limites": self._limites
        }


# ═══ INSTANCIA GLOBAL ═══
_dashboard_instance = None


def get_dashboard() -> SystemDashboard:
    """Retorna instância do Dashboard."""
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = SystemDashboard()
    return _dashboard_instance
