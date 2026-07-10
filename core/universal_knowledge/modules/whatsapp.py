from ..base_module import BaseModule
from typing import Any, Dict, List
import requests
import logging
import os

logger = logging.getLogger(__name__)


class WhatsAppModule(BaseModule):
    def __init__(self):
        super().__init__(
            name="whatsapp",
            description="Enviar e receber mensagens via WhatsApp Business API (Meta Cloud API)"
        )
        self._access_token = None
        self._phone_number_id = None
        self._verify_token = None

    def _load_resources(self):
        logger.info("Carregando recursos do WhatsApp...")

        self._access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self._phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self._verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")

        self._metadata = {
            "version": "1.0",
            "api_version": "v22.0",
            "capabilities": [
                "send_text",
                "send_image",
                "send_document",
                "send_template",
                "send_interactive",
                "mark_as_read",
                "get_media"
            ]
        }

    def _unload_resources(self):
        self._access_token = None
        self._phone_number_id = None
        logger.info("Recursos do WhatsApp liberados")

    def execute(self, action: str, **kwargs) -> Any:
        actions = {
            "send": self._send_text,
            "image": self._send_image,
            "document": self._send_document,
            "template": self._send_template,
            "interactive": self._send_interactive,
            "read": self._mark_as_read
        }

        if action not in actions:
            raise ValueError(f"Ação não suportada: {action}")

        return actions[action](**kwargs)

    def _get_api_url(self, endpoint: str = "messages") -> str:
        return f"https://graph.facebook.com/v22.0/{self._phone_number_id}/{endpoint}"

    def _get_headers(self) -> Dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }

    def _send_text(self, to: str, text: str, **kwargs) -> Dict:
        if not self._access_token:
            raise RuntimeError("WhatsApp Access Token não configurado")

        url = self._get_api_url()
        headers = self._get_headers()

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def _send_image(self, to: str, image_url: str, caption: str = "", **kwargs) -> Dict:
        if not self._access_token:
            raise RuntimeError("WhatsApp Access Token não configurado")

        url = self._get_api_url()
        headers = self._get_headers()

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def _send_document(self, to: str, document_url: str, caption: str = "", **kwargs) -> Dict:
        if not self._access_token:
            raise RuntimeError("WhatsApp Access Token não configurado")

        url = self._get_api_url()
        headers = self._get_headers()

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "caption": caption
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def _send_template(self, to: str, template_name: str, language: str = "pt_BR",
                       parameters: List[str] = None, **kwargs) -> Dict:
        if not self._access_token:
            raise RuntimeError("WhatsApp Access Token não configurado")

        url = self._get_api_url()
        headers = self._get_headers()

        template_data = {
            "name": template_name,
            "language": {"code": language}
        }

        if parameters:
            template_data["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in parameters]
                }
            ]

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": template_data
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def _send_interactive(self, to: str, body_text: str, buttons: List[Dict], **kwargs) -> Dict:
        if not self._access_token:
            raise RuntimeError("WhatsApp Access Token não configurado")

        url = self._get_api_url()
        headers = self._get_headers()

        interactive_buttons = []
        for i, btn in enumerate(buttons[:3]):
            interactive_buttons.append({
                "type": "reply",
                "reply": {
                    "id": btn.get("id", f"btn_{i}"),
                    "title": btn.get("title", f"Opção {i+1}")
                }
            })

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": interactive_buttons}
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def _mark_as_read(self, message_id: str, **kwargs) -> bool:
        if not self._access_token:
            raise RuntimeError("WhatsApp Access Token não configurado")

        url = self._get_api_url()
        headers = self._get_headers()

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.status_code == 200

    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        if mode == "subscribe" and token == self._verify_token:
            return challenge
        raise ValueError("Verificação do webhook falhou")
