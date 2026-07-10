import os
import subprocess
import tempfile
import shutil
import logging
from typing import Dict, Tuple, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class CommandSandbox:
    def __init__(self, temp_dir: str = "data/sandbox"):
        self.temp_dir = temp_dir
        self._ensure_temp_dir()
        self._blocked_paths = [
            os.path.expanduser("~"),
            "C:\\Users",
            "/home",
            "/root",
            "/etc",
            "/var",
            "C:\\Windows",
        ]

    def _ensure_temp_dir(self):
        os.makedirs(self.temp_dir, exist_ok=True)

    def validate_path(self, path: str) -> Tuple[bool, str]:
        abs_path = os.path.abspath(path)

        for blocked in self._blocked_paths:
            if abs_path.startswith(os.path.abspath(blocked)):
                return False, f"Acesso bloqueado: {blocked}"

        if os.path.exists(abs_path):
            if abs_path.startswith(os.path.abspath(self.temp_dir)):
                return True, "Caminho no sandbox permitido"
            else:
                return False, "Acesso a fora do sandbox bloqueado"

        return True, "Caminho permitido"

    def create_sandboxed_env(self) -> str:
        sandbox_id = f"sandbox_{os.urandom(8).hex()}"
        sandbox_path = os.path.join(self.temp_dir, sandbox_id)
        os.makedirs(sandbox_path, exist_ok=True)

        allowed_dirs = ["documents", "downloads", "output"]
        for d in allowed_dirs:
            os.makedirs(os.path.join(sandbox_path, d), exist_ok=True)

        return sandbox_path

    def cleanup_sandbox(self, sandbox_path: str):
        if os.path.exists(sandbox_path):
            shutil.rmtree(sandbox_path)
            logger.info(f"Sandbox limpo: {sandbox_path}")

    def execute_command(self, command: str, sandbox_path: str = None,
                        timeout: int = 30) -> Tuple[bool, str, str]:
        blocked_commands = [
            "curl", "wget", "fetch",
            "Invoke-WebRequest", "Invoke-Expression", "IEX",
            "Start-Process", "System.Diagnostics.Process",
            "bash", "sh", "cmd",
            "eval", "exec", "system", "popen",
            "nc", "netcat", "ncat", "socat",
            "python -e", "perl -e", "ruby -e", "node -e",
        ]

        cmd_lower = command.lower().strip()
        for blocked in blocked_commands:
            if blocked.lower() in cmd_lower:
                return False, "", f"Comando bloqueado: {blocked}"

        if "|" in command or "&&" in command or ";" in command:
            return False, "", "Chaining de comandos bloqueado"

        if ">" in command or ">>" in command:
            return False, "", "Redirecionamento bloqueado"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=sandbox_path or self.temp_dir
            )

            stdout = result.stdout
            stderr = result.stderr

            if len(stdout) > 10000:
                stdout = stdout[:10000] + "\n... [saída truncada]"

            if len(stderr) > 5000:
                stderr = stderr[:5000] + "\n... [saída truncada]"

            return result.returncode == 0, stdout, stderr

        except subprocess.TimeoutExpired:
            return False, "", "Timeout: comando excedeu 30 segundos"
        except Exception as e:
            return False, "", f"Erro ao executar comando: {str(e)}"

    @contextmanager
    def sandboxed_execution(self):
        sandbox_path = self.create_sandboxed_env()
        try:
            yield sandbox_path
        finally:
            self.cleanup_sandbox(sandbox_path)


class FileAccessControl:
    def __init__(self, allowed_dirs: list = None):
        self.allowed_dirs = allowed_dirs or []
        self._sensitive_files = [
            ".env", ".env.local", ".env.production",
            "credentials.json", "token.json",
            "*.key", "*.pem", "*.p12",
            "config.json", "settings.json",
            "*.sqlite", "*.db",
        ]

    def is_path_allowed(self, path: str) -> Tuple[bool, str]:
        abs_path = os.path.abspath(path)

        for pattern in self._sensitive_files:
            if pattern.startswith("*"):
                if abs_path.endswith(pattern[1:]):
                    return False, f"Acesso bloqueado a arquivo sensível: {pattern}"
            elif os.path.basename(abs_path) == pattern:
                return False, f"Acesso bloqueado a arquivo sensível: {pattern}"

        for allowed in self.allowed_dirs:
            if abs_path.startswith(os.path.abspath(allowed)):
                return True, "Acesso permitido"

        return False, "Diretório não autorizado"

    def sanitize_path(self, path: str) -> str:
        path = os.path.normpath(path)

        if ".." in path:
            raise ValueError("Path traversal detectado")

        return path


class NetworkSecurity:
    def __init__(self):
        self._blocked_domains = [
            "pastebin.com",
            "hastebin.com",
            "dpaste.org",
            "rentry.co",
            "ghostbin.co",
        ]
        self._allowed_protocols = ["https"]

    def validate_url(self, url: str) -> Tuple[bool, str]:
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)

            if parsed.scheme not in self._allowed_protocols:
                return False, f"Protocolo bloqueado: {parsed.scheme}"

            if parsed.hostname in self._blocked_domains:
                return False, f"Domínio bloqueado: {parsed.hostname}"

            if parsed.hostname and any(c.isdigit() for c in parsed.hostname.split('.')[0]):
                if not parsed.hostname.replace('.', '').replace('-', '').isalnum():
                    return False, "URL suspeita detectada"

            return True, "URL permitida"

        except Exception as e:
            return False, f"URL inválida: {str(e)}"

    def is_local_request(self, url: str) -> bool:
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""

            local_indicators = [
                "localhost", "127.0.0.1", "0.0.0.0",
                "::1", "[::1]",
                "192.168.", "10.", "172.16.",
            ]

            return any(indicator in hostname for indicator in local_indicators)

        except:
            return False
