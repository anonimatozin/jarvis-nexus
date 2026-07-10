"""
JARVIS Email Agent v1.0
Gerenciamento inteligente de email com IA.

Baseado em: haasonsaas/email-agent
Recursos:
  - Categorização automática de emails
  - Priorização inteligente
  - Resumo de emails longos
  - Resposta automática
  - Integração com Gmail/SMTP
"""
import os
import re
import json
import time
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading

# ═══ DEPENDENCIAS ═══
_email_ok = False
try:
    from email.header import decode_header
    _email_ok = True
except ImportError:
    pass


class EmailAgent:
    """Agente de email inteligente."""

    # Categorias de email
    CATEGORIAS = {
        "importante": ["urgente", "importante", "prioridade", "deadline", "prazo"],
        "trabalho": ["reunião", "projeto", "tarefa", "relatório", "cliente"],
        "financeiro": ["fatura", "pagamento", "boleto", "extrato", "conta"],
        "spam": ["promoção", "oferta", "desconto", "grátis", "clique aqui"],
        "social": ["convite", "evento", "aniversário", "encontro"],
        "notificacao": ["newsletter", "atualização", "notificação", "sistema"]
    }

    def __init__(self, email_user: str = None, email_pass: str = None,
                 imap_server: str = "imap.gmail.com", smtp_server: str = "smtp.gmail.com"):
        self.email_user = email_user or os.getenv("EMAIL_USER", "")
        self.email_pass = email_pass or os.getenv("EMAIL_PASS", "")
        self.imap_server = imap_server
        self.smtp_server = smtp_server
        self._imap = None
        self._smtp = None
        self._emails_cache = []
        self._lock = threading.Lock()

        if not _email_ok:
            print("[EMAIL] Módulo email não disponível")
            return

        if self.email_user and self.email_pass:
            print(f"[EMAIL] Configurado: {self.email_user}")
        else:
            print("[EMAIL] Credenciais não configuradas (EMAIL_USER, EMAIL_PASS)")

    def conectar_imap(self) -> bool:
        """Conecta ao servidor IMAP."""
        if not self.email_user or not self.email_pass:
            return False
        try:
            self._imap = imaplib.IMAP4_SSL(self.imap_server)
            self._imap.login(self.email_user, self.email_pass)
            print(f"[EMAIL] IMAP conectado: {self.imap_server}")
            return True
        except Exception as e:
            print(f"[EMAIL] Erro IMAP: {e}")
            return False

    def conectar_smtp(self) -> bool:
        """Conecta ao servidor SMTP."""
        if not self.email_user or not self.email_pass:
            return False
        try:
            self._smtp = smtplib.SMTP_SSL(self.smtp_server, 465)
            self._smtp.login(self.email_user, self.email_pass)
            print(f"[EMAIL] SMTP conectado: {self.smtp_server}")
            return True
        except Exception as e:
            print(f"[EMAIL] Erro SMTP: {e}")
            return False

    def listar_emails(self, pasta: str = "INBOX", limite: int = 10) -> List[Dict]:
        """Lista emails recentes."""
        if not self._imap:
            if not self.conectar_imap():
                return []

        try:
            self._imap.select(pasta)
            _, data = self._imap.search(None, "ALL")
            email_ids = data[0].split()

            emails = []
            for eid in email_ids[-limite:]:
                _, msg_data = self._imap.fetch(eid, "(RFC822)")
                if msg_data[0]:
                    msg = email.message_from_bytes(msg_data[0][1])
                    remetente = self._decode_header(msg["From"])
                    assunto = self._decode_header(msg["Subject"])
                    data_str = msg["Date"]
                    corpo = self._extrair_corpo(msg)

                    # Categoriza o email
                    categoria = self._categorizar(assunto, corpo)

                    emails.append({
                        "id": eid.decode(),
                        "remetente": remetente,
                        "assunto": assunto,
                        "data": data_str,
                        "categoria": categoria,
                        "corpo_preview": corpo[:200] if corpo else ""
                    })

            with self._lock:
                self._emails_cache = emails

            print(f"[EMAIL] {len(emails)} emails listados")
            return emails
        except Exception as e:
            print(f"[EMAIL] Erro listando: {e}")
            return []

    def _decode_header(self, header: str) -> str:
        """Decodifica header do email."""
        if not header:
            return ""
        try:
            decoded_parts = decode_header(header)
            result = []
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    result.append(part.decode(encoding or "utf-8", errors="ignore"))
                else:
                    result.append(part)
            return " ".join(result)
        except Exception:
            return header

    def _extrair_corpo(self, msg) -> str:
        """Extrai corpo do email."""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode("utf-8", errors="ignore")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode("utf-8", errors="ignore")
        return ""

    def _categorizar(self, assunto: str, corpo: str) -> str:
        """Categoriza email automaticamente."""
        texto = f"{assunto} {corpo}".lower()
        for cat, keywords in self.CATEGORIAS.items():
            for kw in keywords:
                if kw in texto:
                    return cat
        return "outro"

    def resumir_email(self, corpo: str) -> str:
        """Gera resumo do email (usa IA se disponível)."""
        if not corpo:
            return "Corpo vazio"

        # Resumo simples: primeiras frases
        frases = re.split(r'[.!?]+', corpo)
        frases = [f.strip() for f in frases if f.strip()][:3]
        return ". ".join(frases) + "." if frases else corpo[:200]

    def enviar_email(self, para: str, assunto: str, corpo: str) -> bool:
        """Envia email."""
        if not self._smtp:
            if not self.conectar_smtp():
                return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_user
            msg["To"] = para
            msg["Subject"] = assunto
            msg.attach(MIMEText(corpo, "plain", "utf-8"))

            self._smtp.send_message(msg)
            print(f"[EMAIL] Enviado para: {para}")
            return True
        except Exception as e:
            print(f"[EMAIL] Erro enviar: {e}")
            return False

    def responder(self, email_id: str, corpo_resposta: str) -> bool:
        """Responde um email."""
        # Busca o email original
        if not self._imap:
            if not self.conectar_imap():
                return False

        try:
            self._imap.select("INBOX")
            _, data = self._imap.fetch(email_id.encode(), "(RFC822)")
            if data[0]:
                msg = email.message_from_bytes(data[0][1])
                para = msg["From"]
                assunto = f"Re: {self._decode_header(msg['Subject'])}"
                return self.enviar_email(para, assunto, corpo_resposta)
        except Exception as e:
            print(f"[EMAIL] Erro respondendo: {e}")
        return False

    def marcar_lido(self, email_id: str) -> bool:
        """Marca email como lido."""
        if not self._imap:
            return False
        try:
            self._imap.select("INBOX")
            self._imap.store(email_id.encode(), "+FLAGS", "\\Seen")
            return True
        except Exception:
            return False

    def mover(self, email_id: str, pasta: str) -> bool:
        """Move email para outra pasta."""
        if not self._imap:
            return False
        try:
            self._imap.select("INBOX")
            self._imap.copy(email_id.encode(), pasta)
            self._imap.store(email_id.encode(), "+FLAGS", "\\Deleted")
            self._imap.expunge()
            return True
        except Exception:
            return False

    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas de email."""
        with self._lock:
            emails = self._emails_cache

        stats = {
            "total": len(emails),
            "por_categoria": {},
            "por_remetente": {}
        }

        for e in emails:
            cat = e["categoria"]
            stats["por_categoria"][cat] = stats["por_categoria"].get(cat, 0) + 1

            rem = e["remetente"]
            stats["por_remetente"][rem] = stats["por_remetente"].get(rem, 0) + 1

        return stats

    def desconectar(self):
        """Desconecta dos servidores."""
        try:
            if self._imap:
                self._imap.logout()
            if self._smtp:
                self._smtp.quit()
        except Exception:
            pass


# ═══ INSTANCIA GLOBAL ═══
_email_instance = None


def get_email_agent() -> EmailAgent:
    """Retorna instância do Email Agent."""
    global _email_instance
    if _email_instance is None:
        _email_instance = EmailAgent()
    return _email_instance
