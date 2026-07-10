# utils/logger.py
"""
J.A.R.V.I.S. - Sistema de Logs Profissional
Registra todas as atividades do sistema para debug e auditoria.
Usa a biblioteca 'rich' para output colorido e elegante no terminal.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.theme import Theme

# Tema personalizado do Jarvis para o terminal
jarvis_theme = Theme({
    "jarvis": "bold cyan",
    "user": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "system": "bold blue",
    "success": "bold green",
    "info": "dim white",
})

# Console global com tema do Jarvis (forca UTF-8 no Windows)
import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

console = Console(theme=jarvis_theme, force_terminal=True, file=open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1))


def setup_logger(name: str = "jarvis", level: str = "INFO") -> logging.Logger:
    """
    Configura e retorna um logger profissional.
    
    - Saída no terminal com cores (via Rich)
    - Saída em arquivo para auditoria
    - Formato com timestamp, nível e módulo
    
    Args:
        name: Nome do logger
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Evitar duplicação de handlers ao recarregar
    if logger.handlers:
        return logger
    
    # === Handler para arquivo ===
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"jarvis_{datetime.now().strftime('%Y%m%d')}.log"
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Arquivo guarda TUDO
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] [%(name)s.%(funcName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # === Handler para terminal (simplificado, Rich cuida da formatação) ===
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    stream_formatter = logging.Formatter("%(message)s")
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)
    
    return logger


def print_jarvis(message: str):
    """Exibe mensagem do Jarvis no terminal com estilo."""
    console.print(f"  [jarvis]⟡ JARVIS:[/jarvis] {message}")


def print_user(message: str):
    """Exibe mensagem do usuário no terminal com estilo."""
    console.print(f"  [user]◈ USER:[/user] {message}")


def print_system(message: str):
    """Exibe mensagem do sistema no terminal."""
    console.print(f"  [system]⚙ SYSTEM:[/system] {message}")


def print_error(message: str):
    """Exibe mensagem de erro no terminal."""
    console.print(f"  [error]✖ ERROR:[/error] {message}")


def print_success(message: str):
    """Exibe mensagem de sucesso no terminal."""
    console.print(f"  [success]✔ SUCCESS:[/success] {message}")


def print_banner():
    """Exibe o banner de inicialização do Jarvis."""
    banner = """
[cyan]
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
[/cyan]
[dim]Just A Rather Very Intelligent System[/dim]
[dim]Version 1.0.0-alpha | Codename: Genesis[/dim]
    """
    console.print(banner)