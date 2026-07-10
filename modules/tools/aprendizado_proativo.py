# -*- coding: utf-8 -*-
"""
JARVIS Aprendizado Proativo
Detecta padroes de horario/acoes e sugere (1x por dia por padrao).
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


DADOS_FILE = Path(__file__).parent.parent.parent / "data" / "aprendizado_proativo.json"
DADOS_FILE.parent.mkdir(exist_ok=True)


class AprendizadoProativo:
    def __init__(self, callback_voz=None):
        self.callback_voz = callback_voz
        self.historico = []  # lista de {"acao":, "ts":}
        self.sugestoes_hoje = set()  # padroes ja sugeridos hoje
        self.dia_atual = datetime.now().date().isoformat()
        self._carregar()
        print(f"[APRENDIZADO] Pronto. {len(self.historico)} acoes no historico.")

    def _carregar(self):
        if DADOS_FILE.exists():
            try:
                d = json.loads(DADOS_FILE.read_text(encoding="utf-8"))
                self.historico = d.get("historico", [])
                # Reset sugestoes se mudou o dia
                ult_dia = d.get("dia_atual", "")
                if ult_dia == self.dia_atual:
                    self.sugestoes_hoje = set(d.get("sugestoes_hoje", []))
                else:
                    self.sugestoes_hoje = set()
            except Exception:
                pass

    def _salvar(self):
        try:
            DADOS_FILE.write_text(json.dumps({
                "historico": self.historico[-500:],  # mantem ultimos 500
                "sugestoes_hoje": list(self.sugestoes_hoje),
                "dia_atual": self.dia_atual,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def registrar_acao(self, ferramenta, args=None):
        """Toda acao executada passa por aqui."""
        agora = datetime.now()
        self.historico.append({
            "acao": ferramenta,
            "hora": agora.hour,
            "dia_semana": agora.weekday(),  # 0=seg, 6=dom
            "ts": agora.isoformat(),
        })
        self._salvar()

    def detectar_padrao_agora(self):
        """
        Verifica se ha padrao que casa com horario atual.
        Retorna lista de sugestoes [(ferramenta, "msg pro usuario"), ...]
        """
        agora = datetime.now()
        # Reset dia se mudou
        if agora.date().isoformat() != self.dia_atual:
            self.dia_atual = agora.date().isoformat()
            self.sugestoes_hoje = set()
            self._salvar()

        # Agrupa acoes por hora e dia_semana
        contador = defaultdict(int)
        for h in self.historico:
            chave = (h["acao"], h["hora"])
            contador[chave] += 1

        sugestoes = []
        hora_atual = agora.hour

        for (acao, hora), qtd in contador.items():
            # So sugere se:
            # - aconteceu pelo menos 3x
            # - tá na hora atual (+/- 1h)
            # - nao foi sugerido hoje
            if qtd < 3:
                continue
            if abs(hora - hora_atual) > 1:
                continue
            if acao in self.sugestoes_hoje:
                continue

            msg = self._gerar_msg(acao, qtd)
            sugestoes.append((acao, msg))
            self.sugestoes_hoje.add(acao)

        if sugestoes:
            self._salvar()
        return sugestoes

    def _gerar_msg(self, acao, qtd):
        msgs = {
            "organizar_downloads": (
                f"Sir, notei que voce costuma organizar downloads nesse horario. "
                f"Quer que eu faca?"
            ),
            "listar_pasta": (
                f"Sir, voce costuma checar suas pastas agora. Quer que eu liste alguma?"
            ),
            "criar_codigo": (
                f"Sir, voce costuma codar nesse horario. Precisa de algo?"
            ),
            "abrir_programa": (
                f"Sir, voce costuma abrir programas agora. Quer abrir os de costume?"
            ),
        }
        return msgs.get(acao, f"Sir, voce costuma fazer '{acao}' agora. Quer que eu repita?")


_instance = None

def get_aprendizado(callback_voz=None):
    global _instance
    if _instance is None:
        _instance = AprendizadoProativo(callback_voz=callback_voz)
    return _instance
