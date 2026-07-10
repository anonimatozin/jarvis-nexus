from ..base_module import BaseModule
from typing import Any, Dict, List
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os

logger = logging.getLogger(__name__)


class EmailModule(BaseModule):
    def __init__(self):
        super().__init__(
            name="email",
            description="Enviar e receber emails via IMAP/SMTP (genérico)"
        )
        self._imap_server = None
        self._smtp_server = None
        self._email = None
        self._password = None

    def _load_resources(self):
        logger.info("Carregando recursos de email...")

        self._email = os.getenv("EMAIL_ADDRESS")
        self._password = os.getenv("EMAIL_PASSWORD")
        self._imap_server = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
        self._smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")

        self._metadata = {
            "version": "1.0",
            "capabilities": [
                "list_emails",
                "read_email",
                "send_email",
                "search_emails",
                "delete_email",
                "mark_as_read"
            ]
        }

    def _unload_resources(self):
        self._email = None
        self._password = None
        logger.info("Recursos de email liberados")

    def execute(self, action: str, **kwargs) -> Any:
        actions = {
            "list": self._list_emails,
            "read": self._read_email,
            "send": self._send_email,
            "search": self._search_emails,
            "delete": self._delete_email
        }

        if action not in actions:
            raise ValueError(f"Ação não suportada: {action}")

        return actions[action](**kwargs)

    def _connect_imap(self) -> imaplib.IMAP4_SSL:
        imap = imaplib.IMAP4_SSL(self._imap_server)
        imap.login(self._email, self._password)
        return imap

    def _connect_smtp(self) -> smtplib.SMTP_SSL:
        smtp = smtplib.SMTP_SSL(self._smtp_server, 465)
        smtp.login(self._email, self._password)
        return smtp

    def _list_emails(self, folder: str = "INBOX", limit: int = 10, **kwargs) -> List[Dict]:
        if not self._email:
            raise RuntimeError("Credenciais de email não configuradas")

        imap = self._connect_imap()
        imap.select(folder)

        status, messages = imap.search(None, "ALL")
        email_ids = messages[0].split()

        emails = []
        for email_id in email_ids[-limit:]:
            status, msg_data = imap.fetch(email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            emails.append({
                "id": email_id.decode(),
                "from": msg["From"],
                "to": msg["To"],
                "subject": msg["Subject"],
                "date": msg["Date"]
            })

        imap.close()
        imap.logout()
        return emails

    def _read_email(self, email_id: str, folder: str = "INBOX", **kwargs) -> Dict:
        if not self._email:
            raise RuntimeError("Credenciais de email não configuradas")

        imap = self._connect_imap()
        imap.select(folder)

        status, msg_data = imap.fetch(email_id.encode(), "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()

        imap.close()
        imap.logout()

        return {
            "id": email_id,
            "from": msg["From"],
            "to": msg["To"],
            "subject": msg["Subject"],
            "date": msg["Date"],
            "body": body
        }

    def _send_email(self, to: str, subject: str, body: str, **kwargs) -> bool:
        if not self._email:
            raise RuntimeError("Credenciais de email não configuradas")

        msg = MIMEMultipart()
        msg["From"] = self._email
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        smtp = self._connect_smtp()
        smtp.send_message(msg)
        smtp.quit()

        logger.info(f"Email enviado para {to}: {subject}")
        return True

    def _search_emails(self, query: str, folder: str = "INBOX", **kwargs) -> List[Dict]:
        if not self._email:
            raise RuntimeError("Credenciais de email não configuradas")

        imap = self._connect_imap()
        imap.select(folder)

        status, messages = imap.search(None, f'(OR SUBJECT "{query}" FROM "{query}")')
        email_ids = messages[0].split()

        emails = []
        for email_id in email_ids:
            status, msg_data = imap.fetch(email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            emails.append({
                "id": email_id.decode(),
                "from": msg["From"],
                "subject": msg["Subject"],
                "date": msg["Date"]
            })

        imap.close()
        imap.logout()
        return emails

    def _delete_email(self, email_id: str, folder: str = "INBOX", **kwargs) -> bool:
        if not self._email:
            raise RuntimeError("Credenciais de email não configuradas")

        imap = self._connect_imap()
        imap.select(folder)

        imap.store(email_id.encode(), "+FLAGS", "\\Deleted")
        imap.expunge()

        imap.close()
        imap.logout()

        logger.info(f"Email {email_id} deletado")
        return True
