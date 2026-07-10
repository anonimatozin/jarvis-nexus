import importlib
import logging
from typing import Dict, Type, Optional, List
from .base_module import BaseModule, ModuleState
from datetime import datetime, timedelta
import threading
import time

logger = logging.getLogger(__name__)


class ModuleFactory:
    def __init__(self, idle_timeout_minutes: int = 5):
        self._registry: Dict[str, Dict] = {}
        self._instances: Dict[str, BaseModule] = {}
        self._idle_timeout = timedelta(minutes=idle_timeout_minutes)
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._running = True

        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def _cleanup_loop(self):
        while self._running:
            time.sleep(60)
            self._cleanup_idle_modules()

    def _cleanup_idle_modules(self):
        with self._lock:
            now = datetime.now()
            to_deactivate = []

            for name, module in self._instances.items():
                if module.is_active and module.last_used:
                    if now - module.last_used > self._idle_timeout:
                        to_deactivate.append(name)

            for name in to_deactivate:
                logger.info(f"Desativando módulo ocioso: {name}")
                self._instances[name].deactivate()

    def register(self, name: str, module_path: str, class_name: str,
                 description: str = "", keywords: List[str] = None):
        self._registry[name] = {
            "module_path": module_path,
            "class_name": class_name,
            "description": description,
            "keywords": keywords or []
        }
        logger.info(f"Módulo registrado: {name}")

    def register_class(self, name: str, module_class: Type[BaseModule],
                       description: str = "", keywords: List[str] = None):
        self._registry[name] = {
            "class": module_class,
            "description": description,
            "keywords": keywords or []
        }
        logger.info(f"Módulo registrado (classe): {name}")

    def get(self, name: str) -> Optional[BaseModule]:
        if name not in self._registry:
            logger.warning(f"Módulo não registrado: {name}")
            return None

        with self._lock:
            if name not in self._instances:
                success = self._create_instance(name)
                if not success:
                    return None

            module = self._instances[name]

            if module.is_sleeping:
                module.activate()

            module.last_used = datetime.now()
            return module

    def _create_instance(self, name: str) -> bool:
        try:
            registry_info = self._registry[name]

            if "class" in registry_info:
                module_class = registry_info["class"]
            else:
                module_path = registry_info["module_path"]
                class_name = registry_info["class_name"]

                module = importlib.import_module(module_path)
                module_class = getattr(module, class_name)

            instance = module_class()
            self._instances[name] = instance
            logger.info(f"Instância criada: {name}")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar instância do módulo {name}: {e}")
            return False

    def get_all_registered(self) -> List[Dict]:
        result = []
        for name, info in self._registry.items():
            result.append({
                "name": name,
                "description": info.get("description", ""),
                "keywords": info.get("keywords", []),
                "loaded": name in self._instances,
                "state": self._instances[name].state.value if name in self._instances else "not_loaded"
            })
        return result

    def get_active_modules(self) -> List[str]:
        return [name for name, module in self._instances.items() if module.is_active]

    def get_all_instances(self) -> Dict[str, BaseModule]:
        return self._instances.copy()

    def deactivate_all(self):
        with self._lock:
            for module in self._instances.values():
                if module.is_active:
                    module.deactivate()

    def shutdown(self):
        self._running = False
        self.deactivate_all()
        logger.info("ModuleFactory desligada")
