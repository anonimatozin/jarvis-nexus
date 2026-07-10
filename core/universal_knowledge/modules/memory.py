from ..base_module import BaseModule
from typing import Any, Dict, List
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryModule(BaseModule):
    def __init__(self):
        super().__init__(
            name="memory",
            description="Memória de longo prazo - lembrar conversas, preferências e contexto"
        )
        self._memory_file = None
        self._memory = {}

    def _load_resources(self):
        logger.info("Carregando recursos de memória...")

        self._memory_file = "data/jarvis_memory.json"

        if os.path.exists(self._memory_file):
            with open(self._memory_file, 'r', encoding='utf-8') as f:
                self._memory = json.load(f)
        else:
            self._memory = {
                "conversations": [],
                "preferences": {},
                "facts": {},
                "learned_skills": []
            }

        self._metadata = {
            "version": "1.0",
            "capabilities": [
                "remember",
                "recall",
                "forget",
                "get_preferences",
                "set_preference",
                "get_facts",
                "add_fact",
                "search_memory"
            ]
        }

    def _unload_resources(self):
        self._save_memory()
        self._memory = {}
        logger.info("Recursos de memória liberados")

    def _save_memory(self):
        os.makedirs(os.path.dirname(self._memory_file), exist_ok=True)
        with open(self._memory_file, 'w', encoding='utf-8') as f:
            json.dump(self._memory, f, ensure_ascii=False, indent=2)

    def execute(self, action: str, **kwargs) -> Any:
        actions = {
            "remember": self._remember,
            "recall": self._recall,
            "forget": self._forget,
            "get_preferences": self._get_preferences,
            "set_preference": self._set_preference,
            "get_facts": self._get_facts,
            "add_fact": self._add_fact,
            "search": self._search_memory
        }

        if action not in actions:
            raise ValueError(f"Ação não suportada: {action}")

        return actions[action](**kwargs)

    def _remember(self, key: str, value: str, category: str = "general", **kwargs) -> bool:
        entry = {
            "key": key,
            "value": value,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }

        self._memory["conversations"].append(entry)

        if len(self._memory["conversations"]) > 1000:
            self._memory["conversations"] = self._memory["conversations"][-500:]

        self._save_memory()
        return True

    def _recall(self, key: str = None, category: str = None, limit: int = 10, **kwargs) -> List[Dict]:
        conversations = self._memory.get("conversations", [])

        if key:
            conversations = [c for c in conversations if key.lower() in c.get("key", "").lower() or key.lower() in c.get("value", "").lower()]

        if category:
            conversations = [c for c in conversations if c.get("category") == category]

        return conversations[-limit:]

    def _forget(self, key: str, **kwargs) -> bool:
        self._memory["conversations"] = [
            c for c in self._memory["conversations"]
            if c.get("key") != key
        ]
        self._save_memory()
        return True

    def _get_preferences(self, **kwargs) -> Dict:
        return self._memory.get("preferences", {})

    def _set_preference(self, key: str, value: str, **kwargs) -> bool:
        self._memory["preferences"][key] = value
        self._save_memory()
        return True

    def _get_facts(self, **kwargs) -> Dict:
        return self._memory.get("facts", {})

    def _add_fact(self, key: str, value: str, **kwargs) -> bool:
        self._memory["facts"][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._save_memory()
        return True

    def _search_memory(self, query: str, limit: int = 10, **kwargs) -> List[Dict]:
        results = []

        for entry in self._memory.get("conversations", []):
            if query.lower() in str(entry).lower():
                results.append(entry)

        for key, value in self._memory.get("facts", {}).items():
            if query.lower() in key.lower() or query.lower() in str(value).lower():
                results.append({"key": key, "value": value, "category": "fact"})

        return results[-limit:]
