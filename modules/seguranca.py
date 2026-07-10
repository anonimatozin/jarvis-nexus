# modules/seguranca.py
"""
J.A.R.V.I.S. - Módulo de Segurança v1.0
Senhas, logs, alertas e proteção.
"""

import os
import json
import hashlib
import time
import subprocess
import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.logger import setup_logger, print_success, print_error, print_system

logger = setup_logger("seguranca")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

SENHA_FILE = DATA_DIR / "senha_voz.json"
LOGS_FILE = DATA_DIR / "logs_acesso.json"
ALERTAS_FILE = DATA_DIR / "alertas.json"


class Seguranca:
    """Módulo de segurança do Jarvis."""

    def __init__(self):
        self._senha_hash = self._carregar_senha()
        self._logs = self._carregar_logs()
        self._alertas = self._carregar_alertas()
        self._bloqueado = False
        self._ultimo_comando = None
        self._tentativas = 0
        self._max_tentativas = 3

    def _carregar_senha(self) -> Optional[str]:
        try:
            if SENHA_FILE.exists():
                data = json.loads(SENHA_FILE.read_text(encoding="utf-8"))
                return data.get("hash")
        except Exception:
            pass
        return None

    def _salvar_senha(self, hash_senha: str):
        try:
            SENHA_FILE.write_text(
                json.dumps({"hash": hash_senha, "data": datetime.now().isoformat()}),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Erro salvar senha: {e}")

    def _carregar_logs(self) -> List[Dict]:
        try:
            if LOGS_FILE.exists():
                return json.loads(LOGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return []

    def _salvar_logs(self):
        try:
            # Mantém últimos 1000 logs
            self._logs = self._logs[-1000:]
            LOGS_FILE.write_text(
                json.dumps(self._logs, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Erro salvar logs: {e}")

    def _carregar_alertas(self) -> List[Dict]:
        try:
            if ALERTAS_FILE.exists():
                return json.loads(ALERTAS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        return []

    def _salvar_alertas(self):
        try:
            ALERTAS_FILE.write_text(
                json.dumps(self._alertas[-100:], indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Erro salvar alertas: {e}")

    def _hash_senha(self, senha: str) -> str:
        """Gera hash SHA256 da senha."""
        return hashlib.sha256(senha.encode()).hexdigest()

    def registrar_log(self, acao: str, detalhes: str = ""):
        """Registra ação nos logs."""
        log = {
            "timestamp": datetime.now().isoformat(),
            "acao": acao,
            "detalhes": detalhes,
            "hostname": platform.node(),
        }
        self._logs.append(log)
        self._salvar_logs()

    def adicionar_alerta(self, tipo: str, mensagem: str):
        """Adiciona um alerta."""
        alerta = {
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "mensagem": mensagem,
            "lido": False,
        }
        self._alertas.append(alerta)
        self._salvar_alertas()

    # ═══ SENHA ═══

    def definir_senha(self, senha: str) -> str:
        """Define senha por voz."""
        if len(senha) < 4:
            return "Senha muito curta. Mínimo 4 caracteres."
        
        hash_senha = self._hash_senha(senha)
        self._salvar_senha(hash_senha)
        self._senha_hash = hash_senha
        self.registrar_log("senha_definida", "Senha alterada")
        return "Senha definida com sucesso, Sir."

    def verificar_senha(self, senha: str) -> bool:
        """Verifica senha."""
        if not self._senha_hash:
            return True  # Sem senha = acesso livre
        
        hash_input = self._hash_senha(senha)
        if hash_input == self._senha_hash:
            self._tentativas = 0
            return True
        
        self._tentativas += 1
        if self._tentativas >= self._max_tentativas:
            self._bloqueado = True
            self.adicionar_alerta("bloqueio", "Muitas tentativas - sistema bloqueado")
        
        return False

    def desbloquear(self, senha: str) -> str:
        """Desbloqueia o sistema."""
        if self.verificar_senha(senha):
            self._bloqueado = False
            self._tentativas = 0
            self.registrar_log("desbloqueado", "Sistema desbloqueado")
            return "Sistema desbloqueado, Sir."
        restantes = self._max_tentativas - self._tentativas
        return f"Senha incorreta. {restantes} tentativas restantes."

    def esta_bloqueado(self) -> bool:
        """Verifica se está bloqueado."""
        return self._bloqueado

    def status_seguranca(self) -> str:
        """Retorna status de segurança."""
        linhas = ["Status de Segurança:"]
        linhas.append(f"  • Senha: {'Configurada' if self._senha_hash else 'Não configurada'}")
        linhas.append(f"  • Bloqueado: {'Sim' if self._bloqueado else 'Não'}")
        linhas.append(f"  • Tentativas: {self._tentativas}/{self._max_tentativas}")
        linhas.append(f"  • Logs: {len(self._logs)} registros")
        linhas.append(f"  • Alertas: {len(self._alertas)} ({sum(1 for a in self._alertas if not a.get('lido'))} não lidos)")
        return "\n".join(linhas)

    # ═══ LOGS ═══

    def listar_logs(self, limite: int = 10) -> str:
        """Lista logs recentes."""
        if not self._logs:
            return "Nenhum log registrado."
        
        linhas = ["Logs recentes:"]
        for log in self._logs[-limite:]:
            linhas.append(f"  • [{log['timestamp'][:16]}] {log['acao']}: {log.get('detalhes', '')}")
        return "\n".join(linhas)

    # ═══ REDE ═══

    def scan_rede(self) -> str:
        """Scan na rede local."""
        try:
            # Pega IP local
            hostname = socket.gethostname()
            ip_local = socket.gethostbyname(hostname)
            
            # Pega subnet
            parts = ip_local.split('.')
            subnet = f"{parts[0]}.{parts[1]}.{parts[2]}"
            
            linhas = [f"Rede local (IP: {ip_local}):"]
            
            # Scan rápido (apenas gateway e dispositivos comuns)
            dispositivos = []
            for i in [1, 2, 100, 101, 102]:
                ip = f"{subnet}.{i}"
                try:
                    result = subprocess.run(
                        ["ping", "-n", "1", "-w", "100", ip],
                        capture_output=True, timeout=2
                    )
                    if result.returncode == 0:
                        dispositivos.append(ip)
                except Exception:
                    pass
            
            if dispositivos:
                for d in dispositivos:
                    linhas.append(f"  • {d} - Online")
            else:
                linhas.append("  • Nenhum dispositivo detectado")
            
            return "\n".join(linhas)
        except Exception as e:
            return f"Erro ao escanear rede: {e}"

    def portas_abertas(self) -> str:
        """Verifica portas abertas comuns."""
        portas_comuns = [80, 443, 554, 8080, 8443]
        
        linhas = ["Verificação de portas:"]
        
        try:
            hostname = socket.gethostname()
            ip_local = socket.gethostbyname(hostname)
            
            for porta in portas_comuns:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    resultado = sock.connect_ex((ip_local, porta))
                    if resultado == 0:
                        linhas.append(f"  • Porta {porta}: ABERTA")
                    sock.close()
                except Exception:
                    pass
            
            if len(linhas) == 1:
                linhas.append("  • Nenhuma porta aberta detectada")
            
            return "\n".join(linhas)
        except Exception as e:
            return f"Erro ao verificar portas: {e}"

    def quem_usou(self) -> str:
        """Mostra quem usou o PC."""
        if not self._logs:
            return "Nenhum registro de uso."
        
        # Agrupa por data
        usos = {}
        for log in self._logs:
            data = log.get("timestamp", "")[:10]
            if data not in usos:
                usos[data] = 0
            usos[data] += 1
        
        linhas = ["Registro de uso:"]
        for data in sorted(usos.keys(), reverse=True)[:7]:
            linhas.append(f"  • {data}: {usos[data]} ações")
        
        return "\n".join(linhas)


# ═══ SINGLETON ═══

_seguranca_instance = None

def get_seguranca():
    global _seguranca_instance
    if _seguranca_instance is None:
        _seguranca_instance = Seguranca()
    return _seguranca_instance
