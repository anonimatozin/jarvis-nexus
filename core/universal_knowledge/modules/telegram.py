from ..base_module import BaseModule
from typing import Any, Dict, List
import requests
import logging

logger = logging.getLogger(__name__)


class TelegramModule(BaseModule):
    def __init__(self):
        super().__init__(
            name="telegram",
            description="Enviar e receber mensagens via Telegram Bot API"
        )
        self._bot_token = None
        self._chat_id = None

    def _load_resources(self):
        logger.info("Carregando recursos do Telegram...")

        # TODO: Carregar token do .env
        import os
        self._bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self._chat_id = os.getenv("TELEGRAM_CHAT_ID")

        self._metadata = {
            "version": "1.0",
            "capabilities": [
                "send_message",
                "send_photo",
                "send_document",
                "get_updates",
                "set_webhook"
            ]
        }

    def _unload_resources(self):
        self._bot_token = None
        self._chat_id = None
        logger.info("Recursos do Telegram liberados")

    def execute(self, action: str, **kwargs) -> Any:
        actions = {
            "send": self._send_message,
            "photo": self._send_photo,
            "document": self._send_document,
            "updates": self._get_updates
        }

        if action not in actions:
            raise ValueError(f"Ação não suportada: {action}")

        return actions[action](**kwargs)

    def _send_message(self, text: str, chat_id: str = None, **kwargs) -> bool:
        if not self._bot_token:
            raise RuntimeError("Telegram Bot Token não configurado")

        chat_id = chat_id or self._chat_id
        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"

        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        })

        return response.status_code == 200

    def _send_photo(self, photo_url: str, caption: str = "", **kwargs) -> bool:
        if not self._bot_token:
            raise RuntimeError("Telegram Bot Token não configurado")

        url = f"https://api.telegram.org/bot{self._bot_token}/sendPhoto"

        response = requests.post(url, json={
            "chat_id": self._chat_id,
            "photo": photo_url,
            "caption": caption
        })

        return response.status_code == 200

    def _send_document(self, document_url: str, caption: str = "", **kwargs) -> bool:
        if not self._bot_token:
            raise RuntimeError("Telegram Bot Token não configurado")

        url = f"https://api.telegram.org/bot{self._bot_token}/sendDocument"

        response = requests.post(url, json={
            "chat_id": self._chat_id,
            "document": document_url,
            "caption": caption
        })

        return response.status_code == 200

    def _get_updates(self, **kwargs) -> List[Dict]:
        if not self._bot_token:
            raise RuntimeError("Telegram Bot Token não configurado")

        url = f"https://api.telegram.org/bot{self._bot_token}/getUpdates"

        response = requests.get(url, params={"limit": 10})
        data = response.json()

        return data.get("result", [])
