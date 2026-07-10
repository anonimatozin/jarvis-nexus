from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModuleState(Enum):
    SLEEPING = "sleeping"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"


class BaseModule(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.state = ModuleState.SLEEPING
        self._resources_loaded = False
        self.last_used = None
        self.use_count = 0
        self._metadata = {}

    @property
    def is_active(self) -> bool:
        return self.state == ModuleState.ACTIVE

    @property
    def is_sleeping(self) -> bool:
        return self.state == ModuleState.SLEEPING

    def activate(self) -> bool:
        if self.state == ModuleState.ACTIVE:
            return True

        try:
            self.state = ModuleState.LOADING
            logger.info(f"Ativando módulo: {self.name}")

            self._load_resources()
            self._resources_loaded = True
            self.state = ModuleState.ACTIVE
            self.last_used = datetime.now()
            self.use_count += 1

            logger.info(f"Módulo {self.name} ativado com sucesso")
            return True

        except Exception as e:
            self.state = ModuleState.ERROR
            logger.error(f"Erro ao ativar módulo {self.name}: {e}")
            return False

    def deactivate(self):
        if self.state == ModuleState.SLEEPING:
            return

        try:
            logger.info(f"Desativando módulo: {self.name}")
            self._unload_resources()
            self._resources_loaded = False
            self.state = ModuleState.SLEEPING
            logger.info(f"Módulo {self.name} desativado")

        except Exception as e:
            logger.error(f"Erro ao desativar módulo {self.name}: {e}")

    @abstractmethod
    def _load_resources(self):
        pass

    @abstractmethod
    def _unload_resources(self):
        pass

    @abstractmethod
    def execute(self, action: str, **kwargs) -> Any:
        pass

    def get_info(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "state": self.state.value,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "use_count": self.use_count,
            "metadata": self._metadata
        }

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.name}, state={self.state.value})>"
