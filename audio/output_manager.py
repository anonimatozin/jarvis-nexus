"""
Gerenciador de saidas de audio.
Lista devices, salva criptografado, testa.
"""
try:
    import sounddevice as sd
    SD_OK = True
except ImportError:
    SD_OK = False

import numpy as np
import threading

from security.crypto import encrypt, decrypt, mask


def listar_saidas():
    """Retorna lista de devices de saida disponiveis."""
    if not SD_OK:
        return []
    try:
        devices = sd.query_devices()
        saidas = []
        for i, d in enumerate(devices):
            if d.get("max_output_channels", 0) > 0:
                saidas.append({
                    "index": i,
                    "nome": d["name"],
                    "canais": d["max_output_channels"],
                    "sr": int(d.get("default_samplerate", 44100)),
                })
        return saidas
    except Exception as e:
        print(f"[AUDIO] erro listar: {e}")
        return []


def salvar_oficial(nome_device: str):
    """Salva nome do device CRIPTOGRAFADO em hud_settings."""
    from hud_qt import config as cfg
    token = encrypt(nome_device)
    cfg.set_value("audio_output_official_encrypted", token)
    print(f"[AUDIO] Oficial salvo (criptografado): {mask(nome_device)}")


def get_oficial() -> str:
    """Retorna nome do device oficial (descriptografado)."""
    from hud_qt import config as cfg
    token = cfg.get("audio_output_official_encrypted", "")
    if not token:
        return ""
    return decrypt(token)


def get_oficial_mascarado() -> str:
    """Retorna nome mascarado pra mostrar no HUD."""
    nome = get_oficial()
    return mask(nome) if nome else "(nenhum)"


def testar(device_name: str = None, duracao: float = 1.0, freq: float = 440.0):
    """Toca beep de teste no device especificado."""
    if not SD_OK:
        print("[AUDIO] sounddevice indisponivel")
        return False
    try:
        if device_name is None:
            device_name = get_oficial()

        # Encontra index pelo nome
        device_idx = None
        if device_name:
            for s in listar_saidas():
                if device_name.lower() in s["nome"].lower():
                    device_idx = s["index"]
                    break

        sr = 44100
        t = np.linspace(0, duracao, int(sr * duracao), False)
        # Senoide com fade in/out
        tone = 0.3 * np.sin(2 * np.pi * freq * t)
        fade = int(sr * 0.05)
        tone[:fade] *= np.linspace(0, 1, fade)
        tone[-fade:] *= np.linspace(1, 0, fade)

        def play():
            try:
                sd.play(tone, sr, device=device_idx)
                sd.wait()
            except Exception as e:
                print(f"[AUDIO] play erro: {e}")

        threading.Thread(target=play, daemon=True).start()
        return True
    except Exception as e:
        print(f"[AUDIO] testar erro: {e}")
        return False
