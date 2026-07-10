"""
Localizacao - detecta cidade via IP e salva CRIPTOGRAFADA.
"""
import json
import requests
from security.crypto import encrypt, decrypt


def detectar_via_ip():
    """Detecta cidade/regiao/pais via IP publico."""
    # Tenta 3 servicos diferentes (caso um caia)
    servicos = [
        {
            "url": "https://ipapi.co/json/",
            "map": lambda j: {
                "cidade": j.get("city", ""),
                "estado": j.get("region", ""),
                "pais": j.get("country_name", ""),
                "lat": j.get("latitude"),
                "lon": j.get("longitude"),
                "ip": j.get("ip", ""),
            }
        },
        {
            "url": "http://ip-api.com/json/?lang=pt-BR",
            "map": lambda j: {
                "cidade": j.get("city", ""),
                "estado": j.get("regionName", ""),
                "pais": j.get("country", ""),
                "lat": j.get("lat"),
                "lon": j.get("lon"),
                "ip": j.get("query", ""),
            }
        },
        {
            "url": "https://ipwho.is/",
            "map": lambda j: {
                "cidade": j.get("city", ""),
                "estado": j.get("region", ""),
                "pais": j.get("country", ""),
                "lat": j.get("latitude"),
                "lon": j.get("longitude"),
                "ip": j.get("ip", ""),
            }
        },
    ]

    for s in servicos:
        try:
            r = requests.get(s["url"], timeout=5)
            if r.status_code == 200:
                data = s["map"](r.json())
                if data.get("cidade"):
                    print(f"[LOCAL] Detectado: {data['cidade']}, {data['estado']}")
                    return data
        except Exception as e:
            print(f"[LOCAL] Servico {s['url']} falhou: {e}")
            continue

    return None


def salvar_localizacao(dados):
    """Salva localizacao CRIPTOGRAFADA em hud_settings."""
    from hud_qt import config as cfg
    try:
        json_str = json.dumps(dados)
        token = encrypt(json_str)
        cfg.set_value("localizacao_encrypted", token)
        return True
    except Exception as e:
        print(f"[LOCAL] erro salvar: {e}")
        return False


def get_localizacao():
    """Retorna dict de localizacao (descriptografado)."""
    from hud_qt import config as cfg
    token = cfg.get("localizacao_encrypted", "")
    if not token:
        return None
    try:
        json_str = decrypt(token)
        if json_str:
            return json.loads(json_str)
    except Exception as e:
        print(f"[LOCAL] erro decrypt: {e}")
    return None


def get_cidade_atual():
    """Retorna so o nome da cidade."""
    loc = get_localizacao()
    if loc:
        return loc.get("cidade", "")
    return ""


def detectar_e_salvar():
    """Detecta + salva. Retorna a localizacao."""
    dados = detectar_via_ip()
    if dados:
        salvar_localizacao(dados)
        return dados
    return None


def garantir_localizacao():
    """Se nao tem salva, detecta e salva. Senao retorna a salva."""
    loc = get_localizacao()
    if loc:
        return loc
    return detectar_e_salvar()


def mudar_cidade_manual(nome_cidade):
    """Sobrescreve cidade manualmente (mantem outros campos)."""
    loc = get_localizacao() or {}
    loc["cidade"] = nome_cidade
    loc["manual"] = True
    return salvar_localizacao(loc)
