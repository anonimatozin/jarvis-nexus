"""
Clima v3 - Consenso de 3 APIs (wttr.in + Open-Meteo + MET Norway).
Calcula media, variacao e confianca da previsao.
"""
import requests
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.localizacao import get_cidade_atual, get_localizacao


PALAVRAS_IGNORAR = {
    "clima", "tempo", "temperatura", "previsao", "previsão",
    "do", "da", "de", "em", "na", "no", "para",
    "hoje", "amanha", "amanhã", "agora",
    "qual", "como", "esta", "está", "ta", "fica",
    "vai", "chover", "calor", "frio", "quente",
    "jarvis", "sir", "por", "favor", "me", "diz",
    "fala", "conta", "ver", "veja",
}



# Traducao automatica de descricoes em ingles
TRADUCAO_CLIMA_VOZ = {
    "cloudy": "nublado",
    "clear": "ceu limpo",
    "sunny": "ensolarado",
    "rain": "chuva",
    "rainy": "chuvoso",
    "drizzle": "garoa",
    "light rain": "chuva fraca",
    "heavy rain": "chuva forte",
    "thunderstorm": "tempestade",
    "snow": "neve",
    "fog": "neblina",
    "mist": "neblina",
    "overcast": "encoberto",
    "partly cloudy": "parcialmente nublado",
    "partlycloudy": "parcialmente nublado",
    "partlycloudy_day": "parcialmente nublado",
    "partlycloudy_night": "parcialmente nublado a noite",
    "clear_day": "ceu limpo",
    "clear_night": "ceu limpo a noite",
    "cloudy_day": "nublado",
    "cloudy_night": "nublado a noite",
    "rain_day": "chuva",
    "rain_night": "chuva a noite",
}

def traduzir_desc_clima(desc):
    if not desc:
        return desc
    d = str(desc).lower().strip().replace(" ", "")
    # tenta exato sem espaco
    for k, v in TRADUCAO_CLIMA_VOZ.items():
        if k.replace(" ", "") == d:
            return v
    # tenta substring
    d_orig = str(desc).lower().strip()
    for k, v in TRADUCAO_CLIMA_VOZ.items():
        if k in d_orig:
            return v
    return desc


def extrair_cidade(texto):
    """Extrai nome de cidade do texto."""
    if not texto:
        return None
    m = re.search(r"\b(?:em|na|no|de|para|pra)\s+([A-Za-zã-úÀ-Úç\s]+?)(?:\s*$|\?|\.|,)", texto)
    if m:
        cand = m.group(1).strip()
        palavras = [p for p in cand.split() if p.lower() not in PALAVRAS_IGNORAR]
        if palavras:
            return " ".join(palavras).strip()

    palavras_texto = texto.split()
    if len(palavras_texto) >= 2:
        ultimas = []
        for w in reversed(palavras_texto):
            w_limpo = w.strip(",.?!")
            if w_limpo.lower() not in PALAVRAS_IGNORAR and len(w_limpo) >= 3:
                ultimas.insert(0, w_limpo)
                if len(ultimas) >= 4:
                    break
            elif ultimas:
                if w_limpo.lower() in {"do", "da", "de", "dos", "das"}:
                    ultimas.insert(0, w_limpo)
                else:
                    break
        if ultimas:
            cand = " ".join(ultimas).strip()
            if len(cand) >= 3:
                return cand
    return None


def _resolver_coordenadas(cidade=None):
    """
    Resolve coordenadas (lat, lon, nome) da cidade.
    Se cidade=None, usa a salva.
    Retorna: (lat, lon, nome_oficial) ou (None, None, None)
    """
    # Se nao passou cidade, usa a salva (ja tem coords!)
    if not cidade:
        loc = get_localizacao()
        if loc and loc.get("lat") is not None:
            return loc["lat"], loc["lon"], loc.get("cidade", "")

    # Se passou cidade, geocode via Open-Meteo (gratis, sem chave)
    if cidade:
        try:
            url = "https://geocoding-api.open-meteo.com/v1/search"
            r = requests.get(url, params={
                "name": cidade,
                "count": 1,
                "language": "pt",
                "format": "json"
            }, timeout=5)
            if r.status_code == 200:
                j = r.json()
                if j.get("results"):
                    res = j["results"][0]
                    return res["latitude"], res["longitude"], res["name"]
        except Exception as e:
            print(f"[CLIMA] geocode falhou: {e}")

    # Fallback: localizacao salva
    loc = get_localizacao()
    if loc and loc.get("lat") is not None:
        return loc["lat"], loc["lon"], loc.get("cidade", "")
    return None, None, None


# ════════════════════════════════════════════════════════════
# API 1: wttr.in (sem chave)
# ════════════════════════════════════════════════════════════
def _api_wttr(lat, lon, dia=0):
    """dia: 0=hoje, 1=amanha"""
    try:
        url = f"https://wttr.in/{lat},{lon}?format=j1&lang=pt"
        r = requests.get(url, timeout=8, headers={"User-Agent": "curl/jarvis"})
        if r.status_code != 200:
            return None
        j = r.json()
        if dia == 0:
            atual = j["current_condition"][0]
            hoje = j["weather"][0]
            chuva_pct = max(
                int(h.get("chanceofrain", 0))
                for h in hoje.get("hourly", [{"chanceofrain": 0}])
            )
            return {
                "fonte": "wttr.in",
                "temp": int(atual.get("temp_C", 0)),
                "sensacao": int(atual.get("FeelsLikeC", 0)),
                "min": int(hoje.get("mintempC", 0)),
                "max": int(hoje.get("maxtempC", 0)),
                "umidade": int(atual.get("humidity", 0)),
                "vento": int(atual.get("windspeedKmph", 0)),
                "chuva_pct": chuva_pct,
                "desc": atual.get("weatherDesc", [{}])[0].get("value", "?"),
            }
        else:
            if len(j["weather"]) < 2:
                return None
            d = j["weather"][1]
            chuva_pct = max(
                int(h.get("chanceofrain", 0))
                for h in d.get("hourly", [{"chanceofrain": 0}])
            )
            return {
                "fonte": "wttr.in",
                "min": int(d.get("mintempC", 0)),
                "max": int(d.get("maxtempC", 0)),
                "chuva_pct": chuva_pct,
                "desc": d["hourly"][4].get("weatherDesc", [{}])[0].get("value", "?"),
            }
    except Exception as e:
        print(f"[CLIMA wttr] {e}")
        return None


# ════════════════════════════════════════════════════════════
# API 2: Open-Meteo (sem chave, MAIS preciso pra chuva)
# ════════════════════════════════════════════════════════════
def _api_open_meteo(lat, lon, dia=0):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            "timezone": "auto",
            "forecast_days": 3,
        }
        r = requests.get(url, params=params, timeout=8)
        if r.status_code != 200:
            return None
        j = r.json()

        if dia == 0:
            cur = j.get("current", {})
            daily = j.get("daily", {})
            return {
                "fonte": "open-meteo",
                "temp": int(cur.get("temperature_2m", 0)),
                "sensacao": int(cur.get("apparent_temperature", 0)),
                "min": int(daily.get("temperature_2m_min", [0])[0]),
                "max": int(daily.get("temperature_2m_max", [0])[0]),
                "umidade": int(cur.get("relative_humidity_2m", 0)),
                "vento": int(cur.get("wind_speed_10m", 0)),
                "chuva_pct": int(daily.get("precipitation_probability_max", [0])[0]),
                "desc": _wmo_code_pt(cur.get("weather_code", 0)),
            }
        else:
            daily = j.get("daily", {})
            if len(daily.get("temperature_2m_max", [])) < 2:
                return None
            return {
                "fonte": "open-meteo",
                "min": int(daily["temperature_2m_min"][1]),
                "max": int(daily["temperature_2m_max"][1]),
                "chuva_pct": int(daily["precipitation_probability_max"][1]),
                "desc": _wmo_code_pt(daily["weather_code"][1]),
            }
    except Exception as e:
        print(f"[CLIMA open-meteo] {e}")
        return None


def _wmo_code_pt(code):
    """Converte codigo WMO em descricao PT."""
    codes = {
        0: "Limpo",
        1: "Predominantemente limpo", 2: "Parcialmente nublado", 3: "Nublado",
        45: "Neblina", 48: "Neblina com geada",
        51: "Garoa fraca", 53: "Garoa", 55: "Garoa forte",
        61: "Chuva fraca", 63: "Chuva", 65: "Chuva forte",
        66: "Chuva congelante fraca", 67: "Chuva congelante forte",
        71: "Neve fraca", 73: "Neve", 75: "Neve forte",
        77: "Granizo de neve",
        80: "Pancadas de chuva fracas", 81: "Pancadas de chuva", 82: "Pancadas fortes",
        85: "Pancadas de neve", 86: "Pancadas de neve fortes",
        95: "Trovoada", 96: "Trovoada com granizo", 99: "Trovoada forte com granizo",
    }
    return codes.get(int(code), "?")


# ════════════════════════════════════════════════════════════
# API 3: MET Norway (oficial meteorologia da Noruega - mundial)
# ════════════════════════════════════════════════════════════
def _api_met_norway(lat, lon, dia=0):
    try:
        url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
        params = {"lat": lat, "lon": lon}
        headers = {"User-Agent": "JARVIS-NEXUS/1.0 (personal use)"}
        r = requests.get(url, params=params, headers=headers, timeout=8)
        if r.status_code != 200:
            return None
        j = r.json()
        timeseries = j["properties"]["timeseries"]

        if dia == 0:
            agora = timeseries[0]["data"]
            inst = agora["instant"]["details"]
            next_1h = agora.get("next_1_hours", {})
            chuva_mm = next_1h.get("details", {}).get("precipitation_amount", 0)
            # converte mm em probabilidade aproximada
            chuva_pct = min(100, int(chuva_mm * 30)) if chuva_mm > 0 else 0

            # min/max do dia (proximas 24h)
            temps = [t["data"]["instant"]["details"].get("air_temperature", 0)
                     for t in timeseries[:24]]
            return {
                "fonte": "met.no",
                "temp": int(inst.get("air_temperature", 0)),
                "sensacao": int(inst.get("air_temperature", 0)),
                "min": int(min(temps)) if temps else 0,
                "max": int(max(temps)) if temps else 0,
                "umidade": int(inst.get("relative_humidity", 0)),
                "vento": int(inst.get("wind_speed", 0) * 3.6),  # m/s -> km/h
                "chuva_pct": chuva_pct,
                "desc": next_1h.get("summary", {}).get("symbol_code", "?"),
            }
        else:
            # Pega slot ~24-48h
            slots = timeseries[24:48] if len(timeseries) >= 48 else timeseries[24:]
            if not slots:
                return None
            temps = [t["data"]["instant"]["details"].get("air_temperature", 0)
                     for t in slots]
            chuvas = []
            for t in slots:
                next_1h = t["data"].get("next_1_hours", {})
                if next_1h:
                    chuvas.append(next_1h.get("details", {}).get("precipitation_amount", 0))
            chuva_total = sum(chuvas)
            chuva_pct = min(100, int(chuva_total * 15)) if chuva_total > 0 else 0

            return {
                "fonte": "met.no",
                "min": int(min(temps)) if temps else 0,
                "max": int(max(temps)) if temps else 0,
                "chuva_pct": chuva_pct,
                "desc": "?",
            }
    except Exception as e:
        print(f"[CLIMA met.no] {e}")
        return None


# ════════════════════════════════════════════════════════════
# CONSENSO - chama 3 APIs em paralelo e calcula
# ════════════════════════════════════════════════════════════
def _consultar_consenso(lat, lon, dia=0):
    """Consulta 3 APIs em paralelo, retorna lista de resultados."""
    resultados = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_api_wttr, lat, lon, dia): "wttr",
            executor.submit(_api_open_meteo, lat, lon, dia): "open-meteo",
            executor.submit(_api_met_norway, lat, lon, dia): "met.no",
        }
        for future in as_completed(futures, timeout=15):
            try:
                r = future.result(timeout=10)
                if r:
                    resultados.append(r)
            except Exception as e:
                print(f"[CONSENSO] erro {futures[future]}: {e}")
    return resultados


def _calcular_consenso(resultados, dia=0):
    """Calcula media e confianca dos resultados."""
    if not resultados:
        return None

    n = len(resultados)
    consenso = {
        "fontes_consultadas": n,
        "fontes": [r["fonte"] for r in resultados],
    }

    # Min/max (media)
    mins = [r.get("min", 0) for r in resultados if "min" in r]
    maxs = [r.get("max", 0) for r in resultados if "max" in r]
    if mins:
        consenso["min"] = round(sum(mins) / len(mins))
    if maxs:
        consenso["max"] = round(sum(maxs) / len(maxs))

    # Hoje: temp atual
    if dia == 0:
        temps = [r.get("temp", 0) for r in resultados if "temp" in r]
        sensacoes = [r.get("sensacao", 0) for r in resultados if "sensacao" in r]
        umidades = [r.get("umidade", 0) for r in resultados if "umidade" in r]
        ventos = [r.get("vento", 0) for r in resultados if "vento" in r]
        if temps:
            consenso["temp"] = round(sum(temps) / len(temps))
            consenso["temp_min_fonte"] = min(temps)
            consenso["temp_max_fonte"] = max(temps)
        if sensacoes:
            consenso["sensacao"] = round(sum(sensacoes) / len(sensacoes))
        if umidades:
            consenso["umidade"] = round(sum(umidades) / len(umidades))
        if ventos:
            consenso["vento"] = round(sum(ventos) / len(ventos))

    # Chuva (a parte mais importante!)
    chuvas = [r.get("chuva_pct", 0) for r in resultados if "chuva_pct" in r]
    if chuvas:
        consenso["chuva_pct"] = round(sum(chuvas) / len(chuvas))
        consenso["chuva_min"] = min(chuvas)
        consenso["chuva_max"] = max(chuvas)
        # Concordancia: variacao entre fontes
        variacao = max(chuvas) - min(chuvas)
        if variacao <= 15:
            consenso["confianca"] = "alta"
        elif variacao <= 35:
            consenso["confianca"] = "media"
        else:
            consenso["confianca"] = "baixa"
        consenso["chuva_variacao"] = variacao

    # Descricao (pega a primeira nao "?")
    for r in resultados:
        if r.get("desc") and r["desc"] != "?":
            consenso["desc"] = r["desc"]
            break

    return consenso


# ════════════════════════════════════════════════════════════
# API PUBLICA - usado pelo engine
# ════════════════════════════════════════════════════════════
def get_clima_atual(cidade=None):
    lat, lon, nome = _resolver_coordenadas(cidade)
    if lat is None:
        return {"erro": "Cidade nao localizada"}

    # Usa nome pedido se o usuario especificou
    nome_final = cidade if cidade else nome

    resultados = _consultar_consenso(lat, lon, dia=0)
    if not resultados:
        return {"erro": "Todas as APIs falharam"}

    c = _calcular_consenso(resultados, dia=0)
    c["cidade"] = nome_final
    return c


def get_previsao(cidade=None, dias=2):
    lat, lon, nome = _resolver_coordenadas(cidade)
    if lat is None:
        return {"erro": "Cidade nao localizada"}

    nome_final = cidade if cidade else nome
    resultado = {"cidade": nome_final, "previsoes": []}

    for d in range(min(dias, 2)):
        resultados = _consultar_consenso(lat, lon, dia=d)
        if resultados:
            c = _calcular_consenso(resultados, dia=d)
            resultado["previsoes"].append(c)
    return resultado


def falar_clima_atual(cidade=None):
    c = get_clima_atual(cidade)
    if c.get("erro"):
        return f"Nao consegui ver o clima, Sir. {c['erro']}"

    fontes = c.get("fontes_consultadas", 0)
    msg = (
        f"Em {c['cidade']}, {c.get('temp', '?')} graus, "
        f"sensacao de {c.get('sensacao', '?')}. "
    )
    if c.get("desc"):
        msg += f"{c['desc']}. "
    msg += f"Umidade {c.get('umidade', '?')} por cento, "
    msg += f"vento {c.get('vento', '?')} km/h. "
    msg += f"Consenso de {fontes} fontes."
    return msg


def falar_previsao(cidade=None, dia_alvo="hoje"):
    idx = 1 if dia_alvo == "amanha" else 0
    p = get_previsao(cidade, dias=idx + 1)

    if p.get("erro"):
        return f"Nao consegui a previsao, Sir."
    if not p.get("previsoes") or idx >= len(p["previsoes"]):
        return "Sem dados pra esse dia, Sir."

    c = p["previsoes"][idx]
    nome_dia = "Amanha" if dia_alvo == "amanha" else "Hoje"
    chuva = c.get("chuva_pct", 0)
    chuva_min = c.get("chuva_min", chuva)
    chuva_max = c.get("chuva_max", chuva)
    confianca = c.get("confianca", "media")
    fontes = c.get("fontes_consultadas", 0)

    msg = (
        f"{nome_dia} em {p['cidade']}: "
        f"minima {c.get('min', '?')}, maxima {c.get('max', '?')} graus. "
    )

    # Chuva com consenso
    if chuva >= 60:
        msg += f"Chance ALTA de chuva: {chuva} por cento. "
    elif chuva >= 30:
        msg += f"Chance moderada de chuva: {chuva} por cento. "
    elif chuva >= 10:
        msg += f"Chance baixa de chuva: {chuva} por cento. "
    else:
        msg += "Sem chuva prevista. "

    # Confianca
    if confianca == "alta":
        msg += f"Consenso forte entre {fontes} fontes."
    elif confianca == "media":
        msg += f"Fontes concordam parcialmente (variacao de {chuva_max - chuva_min} pontos)."
    else:
        msg += f"Fontes discordam: variam de {chuva_min} a {chuva_max} por cento."

    return msg
