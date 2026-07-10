# modules/produtividade.py
"""
J.A.R.V.I.S. - Módulo de Produtividade v1.0
Relatórios, planilhas, tempo focado e organização.
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from collections import defaultdict

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.logger import setup_logger, print_success, print_error, print_system

logger = setup_logger("produtividade")


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


class Produtividade:
    """Módulo de produtividade e relatórios."""

    def __init__(self, context_detector=None, memory=None, brain=None):
        self.context = context_detector
        self.memory = memory
        self.brain = brain

        self._gastos_file = DATA_DIR / "gastos.json"
        self._gastos = self._carregar_gastos()

        self._stats_file = DATA_DIR / "stats_produtividade.json"
        self._stats = self._carregar_stats()

        self._tracking = False
        self._track_thread = None
        self._tempo_focado = 0  # minutos focados hoje
        self._ultimo_check = None

        # Importa gerador de planilhas
        from modules.planilhas import get_planilhas_generator
        self.planilhas = get_planilhas_generator()

    def _carregar_gastos(self) -> List[Dict]:
        try:
            if self._gastos_file.exists():
                return json.loads(self._gastos_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return []

    def _salvar_gastos(self):
        try:
            self._gastos_file.write_text(
                json.dumps(self._gastos, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Erro salvar gastos: {e}")

    def _carregar_stats(self) -> Dict:
        try:
            if self._stats_file.exists():
                data = json.loads(self._stats_file.read_text(encoding="utf-8"))
                # Reset diário
                if data.get("data") != datetime.now().strftime("%Y-%m-%d"):
                    return self._stats_novos()
                return data
        except Exception:
            pass
        return self._stats_novos()

    def _stats_novos(self) -> Dict:
        return {
            "data": datetime.now().strftime("%Y-%m-%d"),
            "comandos_jarvis": 0,
            "memorias_criadas": 0,
            "tarefas_concluidas": 0,
            "tempo_focado_min": 0,
            "apps_usados": {},
            "historico": [],
        }

    def _salvar_stats(self):
        try:
            self._stats_file.write_text(
                json.dumps(self._stats, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Erro salvar stats: {e}")

    def registrar_comando(self):
        """Registra uso de comando Jarvis."""
        self._stats["comandos_jarvis"] = self._stats.get("comandos_jarvis", 0) + 1
        self._salvar_stats()

    def registrar_memoria(self):
        """Registra criação de memória."""
        self._stats["memorias_criadas"] = self._stats.get("memorias_criadas", 0) + 1
        self._salvar_stats()

    def registrar_tarefa(self):
        """Registra tarefa concluída."""
        self._stats["tarefas_concluidas"] = self._stats.get("tarefas_concluidas", 0) + 1
        self._salvar_stats()

    def registrar_app(self, nome_app: str, minutos: int = 1):
        """Registra tempo em um app."""
        apps = self._stats.get("apps_usados", {})
        apps[nome_app] = apps.get(nome_app, 0) + minutos
        self._stats["apps_usados"] = apps
        self._salvar_stats()

    def iniciar_tracking(self):
        """Inicia tracking de foco em background."""
        if self._tracking:
            return
        self._tracking = True
        self._track_thread = threading.Thread(target=self._tracking_loop, daemon=True)
        self._track_thread.start()
        print_system("[PROD] Tracking de foco iniciado.")

    def parar_tracking(self):
        """Para tracking de foco."""
        self._tracking = False
        print_system("[PROD] Tracking de foco parado.")

    def _tracking_loop(self):
        """Loop de tracking - checa a cada 30s."""
        while self._tracking:
            try:
                if self.context and self.context.disponivel:
                    app = self.context.app_foco_atual()
                    if app and app not in ("Explorador", "Windows Desktop"):
                        self._tempo_focado += 0.5  # 30 segundos
                        self._stats["tempo_focado_min"] = int(self._tempo_focado)
                        self.registrar_app(app, 0.5)
            except Exception:
                pass
            time.sleep(30)

    def tempo_focado_hoje(self) -> str:
        """Retorna tempo focado formatado."""
        min_total = int(self._tempo_focado)
        horas = min_total // 60
        mins = min_total % 60
        if horas > 0:
            return f"{horas}h{mins:02d}min"
        return f"{mins}min"

    def resumo_dia(self) -> str:
        """Retorna resumo do dia em texto."""
        stats = self._stats
        apps = stats.get("apps_usados", {})
        top_apps = sorted(apps.items(), key=lambda x: -x[1])[:5]

        linhas = [
            f"Resumo do dia {stats.get('data', '?')}:",
            f"• Comandos Jarvis: {stats.get('comandos_jarvis', 0)}",
            f"• Memórias criadas: {stats.get('memorias_criadas', 0)}",
            f"• Tarefas concluídas: {stats.get('tarefas_concluidas', 0)}",
            f"• Tempo focado: {self.tempo_focado_hoje()}",
        ]

        if top_apps:
            linhas.append("\nTop apps:")
            for app, tempo in top_apps:
                horas = tempo / 60
                linhas.append(f"  • {app}: {horas:.1f}h")

        return "\n".join(linhas)

    def criar_relatorio_dia(self) -> str:
        """Gera relatório do dia em planilha."""
        apps = self._stats.get("apps_usados", [])
        if isinstance(apps, dict):
            apps_lista = [{"nome": k, "tempo_min": int(v)} for k, v in apps.items()]
            apps_lista.sort(key=lambda x: -x["tempo_min"])
        else:
            apps_lista = apps

        dados = {
            "data": self._stats.get("data", datetime.now().strftime("%Y-%m-%d")),
            "apps_usados": apps_lista,
            "comandos_jarvis": self._stats.get("comandos_jarvis", 0),
            "memorias_criadas": self._stats.get("memorias_criadas", 0),
            "tarefas_concluidas": self._stats.get("tarefas_concluidas", 0),
            "tempo_focado_min": int(self._tempo_focado),
        }

        try:
            caminho = self.planilhas.gerar_relatorio_diano(dados)
            return f"Relatório salvo em: {caminho}"
        except Exception as e:
            return f"Erro ao gerar relatório: {e}"

    def exportar_memorias(self) -> str:
        """Exporta todas as memórias para planilha."""
        if not self.memory:
            return "Memória não disponível para exportação."

        try:
            memorias = self.memory.listar_memorias(limit=1000)
            if not memorias:
                return "Nenhuma memória para exportar."

            memorias_dicts = []
            for mem in memorias:
                memorias_dicts.append({
                    "timestamp": mem[1] if len(mem) > 1 else "",
                    "categoria": mem[2] if len(mem) > 2 else "",
                    "texto": mem[3] if len(mem) > 3 else str(mem),
                })

            caminho = self.planilhas.exportar_memorias(memorias_dicts)
            return f"Memórias exportadas para: {caminho}"
        except Exception as e:
            return f"Erro ao exportar memórias: {e}"

    def resumo_semanal(self) -> str:
        """Gera resumo semanal."""
        # Pega stats dos últimos 7 dias
        dias = []
        for i in range(6, -1, -1):
            data = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            stats_file = DATA_DIR / "stats_produtividade.json"
            try:
                if stats_file.exists():
                    all_stats = json.loads(stats_file.read_text(encoding="utf-8"))
                    # Se for o dia atual, usa as stats em memória
                    if data == datetime.now().strftime("%Y-%m-%d"):
                        dias.append({
                            "data": data,
                            "comandos": self._stats.get("comandos_jarvis", 0),
                            "focado_min": int(self._tempo_focado),
                        })
                    else:
                        dias.append({"data": data, "comandos": 0, "focado_min": 0})
            except Exception:
                dias.append({"data": data, "comandos": 0, "focado_min": 0})

        total_comandos = sum(d.get("comandos", 0) for d in dias)
        total_focado = sum(d.get("focado_min", 0) for d in dias)

        dados_semana = {
            "periodo": f"{dias[0]['data']} a {dias[-1]['data']}" if dias else "Semana",
            "dias": dias,
            "total_comandos": total_comandos,
            "total_focado_min": total_focado,
            "media_diaria_comandos": round(total_comandos / 7, 1),
            "media_diaria_focado_h": round(total_focado / 7 / 60, 1),
        }

        try:
            caminho = self.planilhas.gerar_resumo_semanal(dados_semana)
            return f"Resumo semanal salvo em: {caminho}"
        except Exception as e:
            return f"Erro ao gerar resumo semanal: {e}"

    # ═══ GASTOS ═══

    def adicionar_gasto(self, descricao: str, valor: float, categoria: str = "Outros") -> str:
        """Adiciona um gasto."""
        gasto = {
            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "descricao": descricao,
            "valor": valor,
            "categoria": categoria,
        }
        self._gastos.append(gasto)
        self._salvar_gastos()
        return f"Gasto registrado: {descricao} - R${valor:.2f} ({categoria})"

    def listar_gastos(self, dias: int = 7) -> str:
        """Lista gastos recentes."""
        cutoff = datetime.now() - timedelta(days=dias)
        recentes = []
        for g in self._gastos:
            try:
                data_gasto = datetime.strptime(g["data"], "%Y-%m-%d %H:%M")
                if data_gasto >= cutoff:
                    recentes.append(g)
            except Exception:
                pass

        if not recentes:
            return f"Nenhum gasto nos últimos {dias} dias."

        total = sum(g.get("valor", 0) for g in recentes)
        linhas = [f"Gastos últimos {dias} dias (total: R${total:.2f}):"]
        for g in recentes[-10:]:  # últimos 10
            linhas.append(f"  • {g['data']}: {g['descricao']} - R${g['valor']:.2f}")

        return "\n".join(linhas)

    def planilha_gastos(self) -> str:
        """Gera planilha de gastos."""
        if not self._gastos:
            return "Nenhum gasto registrado."

        try:
            caminho = self.planilhas.gerar_planilha_gastos(self._gastos)
            return f"Planilha de gastos salva em: {caminho}"
        except Exception as e:
            return f"Erro ao gerar planilha: {e}"

    def listar_relatorios(self) -> str:
        """Lista relatórios salvos."""
        relatorios = self.planilhas.listar_relatorios()
        if not relatorios:
            return "Nenhum relatório salvo."

        linhas = ["Relatórios salvos:"]
        for r in relatorios[:15]:
            linhas.append(f"  📄 {r}")
        return "\n".join(linhas)


# ═══ FUNCOES DE INTEGRAÇÃO ═══

_produtividade_instance = None

def get_produtividade(context_detector=None, memory=None, brain=None):
    global _produtividade_instance
    if _produtividade_instance is None:
        _produtividade_instance = Produtividade(
            context_detector=context_detector,
            memory=memory,
            brain=brain,
        )
    return _produtividade_instance
