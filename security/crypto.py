"""
Criptografia de configs sensiveis.
Usa AES-256 (Fernet) com chave derivada do Machine ID do Windows.
"""
import os
import base64
import hashlib
import subprocess
from pathlib import Path

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False


def _get_machine_id():
    """Pega ID unico do PC (Windows). Cai pra hostname se falhar."""
    try:
        # Windows: registry MachineGuid
        result = subprocess.run(
            ["reg", "query",
             r"HKLM\SOFTWARE\Microsoft\Cryptography",
             "/v", "MachineGuid"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split("\n"):
            if "MachineGuid" in line:
                parts = line.split()
                if len(parts) >= 3:
                    return parts[-1].strip()
    except Exception:
        pass
    # Fallback
    import socket
    return socket.gethostname()


def _derive_key():
    """Deriva chave de 32 bytes a partir do machine id."""
    machine = _get_machine_id()
    salt = b"JARVIS_NEXUS_V22_STARK"
    h = hashlib.pbkdf2_hmac("sha256", machine.encode(), salt, 100000)
    return base64.urlsafe_b64encode(h)


def encrypt(plain_text: str) -> str:
    """Criptografa string."""
    if not CRYPTO_OK or not plain_text:
        return plain_text
    try:
        f = Fernet(_derive_key())
        token = f.encrypt(plain_text.encode())
        return token.decode()
    except Exception as e:
        print(f"[CRYPTO] encrypt erro: {e}")
        return ""


def decrypt(token: str) -> str:
    """Descriptografa string."""
    if not CRYPTO_OK or not token:
        return ""
    try:
        f = Fernet(_derive_key())
        plain = f.decrypt(token.encode())
        return plain.decode()
    except InvalidToken:
        print("[CRYPTO] token invalido (PC diferente ou corrupto)")
        return ""
    except Exception as e:
        print(f"[CRYPTO] decrypt erro: {e}")
        return ""


def mask(text: str, visible_chars: int = 4) -> str:
    """Mascara string pra exibicao (ex: 'Speak***Bluetooth')."""
    if not text:
        return ""
    if len(text) <= visible_chars * 2:
        return "*" * len(text)
    return text[:visible_chars] + "*" * 8 + text[-visible_chars:]
