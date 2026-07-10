from ..base_module import BaseModule
from typing import Any, Dict, List
import os
import subprocess
import psutil
import logging

logger = logging.getLogger(__name__)


class SystemModule(BaseModule):
    def __init__(self):
        super().__init__(
            name="system",
            description="Controle do sistema: arquivos, processos, rede, áudio, hardware"
        )
        self._initialized = False

    def _load_resources(self):
        logger.info("Carregando recursos do sistema...")

        self._metadata = {
            "version": "1.0",
            "capabilities": [
                "list_files",
                "read_file",
                "write_file",
                "delete_file",
                "open_program",
                "close_program",
                "system_info",
                "cpu_usage",
                "memory_usage",
                "disk_usage",
                "list_processes"
            ]
        }
        self._initialized = True

    def _unload_resources(self):
        self._initialized = False
        logger.info("Recursos do sistema liberados")

    def execute(self, action: str, **kwargs) -> Any:
        actions = {
            "list_files": self._list_files,
            "read_file": self._read_file,
            "write_file": self._write_file,
            "delete_file": self._delete_file,
            "open_program": self._open_program,
            "close_program": self._close_program,
            "info": self._system_info,
            "cpu": self._cpu_usage,
            "memory": self._memory_usage,
            "disk": self._disk_usage,
            "processes": self._list_processes
        }

        if action not in actions:
            raise ValueError(f"Ação não suportada: {action}")

        return actions[action](**kwargs)

    def _list_files(self, path: str = ".", **kwargs) -> List[Dict]:
        files = []
        for item in os.scandir(path):
            files.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0
            })
        return files

    def _read_file(self, path: str, **kwargs) -> str:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _write_file(self, path: str, content: str, **kwargs) -> bool:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    def _delete_file(self, path: str, **kwargs) -> bool:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
        return True

    def _open_program(self, program: str, **kwargs) -> bool:
        subprocess.Popen(program, shell=True)
        return True

    def _close_program(self, program: str, **kwargs) -> bool:
        subprocess.run(["taskkill", "/F", "/IM", program], capture_output=True)
        return True

    def _system_info(self, **kwargs) -> Dict:
        return {
            "platform": os.name,
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_total": psutil.virtual_memory().total,
            "memory_used": psutil.virtual_memory().used,
            "memory_percent": psutil.virtual_memory().percent
        }

    def _cpu_usage(self, **kwargs) -> float:
        return psutil.cpu_percent(interval=1)

    def _memory_usage(self, **kwargs) -> Dict:
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": mem.percent
        }

    def _disk_usage(self, path: str = "C:\\", **kwargs) -> Dict:
        disk = psutil.disk_usage(path)
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }

    def _list_processes(self, **kwargs) -> List[Dict]:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            processes.append(proc.info)
        return processes[:20]
