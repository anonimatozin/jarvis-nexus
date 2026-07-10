"""
JARVIS API Integrations v1.0
Integrações com APIs externas (social media, cloud, serviços).

Recursos:
  - Twitter/X API
  - GitHub API
  - Weather API
  - News API
  - Spotify API
  - Telegram Bot
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading

# ═══ DEPENDENCIAS ═══
_requests_ok = False
try:
    import requests
    _requests_ok = True
except ImportError:
    pass


class TwitterAPI:
    """Integração com Twitter/X API."""

    def __init__(self, bearer_token: str = None):
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN", "")
        self.base_url = "https://api.twitter.com/2"
        self._headers = {"Authorization": f"Bearer {self.bearer_token}"}

    def buscar_tweets(self, query: str, limite: int = 10) -> List[Dict]:
        """Busca tweets por query."""
        if not self.bearer_token or not _requests_ok:
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/tweets/search/recent",
                headers=self._headers,
                params={"query": query, "max_results": limite},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
        except Exception as e:
            print(f"[TWITTER] Erro: {e}")
        return []

    def obter_trending(self, woeid: int = 1) -> List[Dict]:
        """Obtém tendências."""
        if not self.bearer_token or not _requests_ok:
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/trends/by/woeid/{woeid}",
                headers=self._headers,
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("trends", [])
        except Exception:
            pass
        return []


class GitHubAPI:
    """Integração com GitHub API."""

    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
        self._headers = {}
        if self.token:
            self._headers["Authorization"] = f"token {self.token}"

    def buscar_repositorios(self, query: str, limite: int = 10) -> List[Dict]:
        """Busca repositórios."""
        if not _requests_ok:
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/search/repositories",
                headers=self._headers,
                params={"q": query, "per_page": limite},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("items", [])
        except Exception as e:
            print(f"[GITHUB] Erro: {e}")
        return []

    def obter_repositorio(self, owner: str, repo: str) -> Optional[Dict]:
        """Obtém detalhes de um repositório."""
        if not _requests_ok:
            return None

        try:
            resp = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}",
                headers=self._headers,
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

    def obter_issues(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """Lista issues de um repositório."""
        if not _requests_ok:
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                headers=self._headers,
                params={"state": state},
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return []

    def criar_issue(self, owner: str, repo: str, titulo: str, corpo: str) -> Optional[Dict]:
        """Cria uma issue."""
        if not self.token or not _requests_ok:
            return None

        try:
            resp = requests.post(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                headers=self._headers,
                json={"title": titulo, "body": corpo},
                timeout=10
            )
            if resp.status_code == 201:
                return resp.json()
        except Exception:
            pass
        return None


class WeatherAPI:
    """Integração com API de clima (OpenWeatherMap)."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY", "")
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def obter_clima(self, cidade: str) -> Optional[Dict]:
        """Obtém clima atual."""
        if not self.api_key or not _requests_ok:
            return None

        try:
            resp = requests.get(
                f"{self.base_url}/weather",
                params={"q": cidade, "appid": self.api_key, "units": "metric", "lang": "pt"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "cidade": data["name"],
                    "temperatura": data["main"]["temp"],
                    "sensacao": data["main"]["feels_like"],
                    "umidade": data["main"]["humidity"],
                    "descricao": data["weather"][0]["description"],
                    "vento": data["wind"]["speed"],
                    "pais": data["sys"]["country"]
                }
        except Exception as e:
            print(f"[WEATHER] Erro: {e}")
        return None

    def obter_previsao(self, cidade: str, dias: int = 5) -> List[Dict]:
        """Obtém previsão do tempo."""
        if not self.api_key or not _requests_ok:
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/forecast",
                params={"q": cidade, "appid": self.api_key, "units": "metric", "lang": "pt", "cnt": dias * 8},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                previsoes = []
                for item in data.get("list", []):
                    previsoes.append({
                        "data": item["dt_txt"],
                        "temperatura": item["main"]["temp"],
                        "descricao": item["weather"][0]["description"],
                        "chuva": item.get("rain", {}).get("3h", 0)
                    })
                return previsoes
        except Exception:
            pass
        return []


class NewsAPI:
    """Integração com News API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY", "")
        self.base_url = "https://newsapi.org/v2"

    def obter_noticias(self, pais: str = "br", categoria: str = None, limite: int = 10) -> List[Dict]:
        """Obtém notícias recentes."""
        if not self.api_key or not _requests_ok:
            return []

        try:
            endpoint = f"{self.base_url}/top-headlines"
            params = {"country": pais, "pageSize": limite, "apiKey": self.api_key}
            if categoria:
                params["category"] = categoria

            resp = requests.get(endpoint, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("articles", [])
        except Exception as e:
            print(f"[NEWS] Erro: {e}")
        return []

    def buscar_noticias(self, query: str, limite: int = 10) -> List[Dict]:
        """Busca notícias por query."""
        if not self.api_key or not _requests_ok:
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/everything",
                params={"q": query, "pageSize": limite, "apiKey": self.api_key, "language": "pt"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("articles", [])
        except Exception:
            pass
        return []


class SpotifyAPI:
    """Integração com Spotify Web API."""

    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET", "")
        self.base_url = "https://api.spotify.com/v1"
        self._token = None
        self._token_expiry = 0

    def _obter_token(self) -> Optional[str]:
        """Obtém token de acesso."""
        if self._token and time.time() < self._token_expiry:
            return self._token

        if not self.client_id or not self.client_secret or not _requests_ok:
            return None

        try:
            resp = requests.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                self._token = data["access_token"]
                self._token_expiry = time.time() + data.get("expires_in", 3600)
                return self._token
        except Exception:
            pass
        return None

    def buscar_musicas(self, query: str, limite: int = 10) -> List[Dict]:
        """Busca músicas no Spotify."""
        token = self._obter_token()
        if not token:
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": query, "type": "track", "limit": limite},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                tracks = data.get("tracks", {}).get("items", [])
                return [{
                    "nome": t["name"],
                    "artista": t["artists"][0]["name"],
                    "album": t["album"]["name"],
                    "duracao_ms": t["duration_ms"],
                    "url": t["external_urls"]["spotify"]
                } for t in tracks]
        except Exception:
            pass
        return []

    def buscar_artistas(self, query: str, limite: int = 5) -> List[Dict]:
        """Busca artistas."""
        token = self._obter_token()
        if not token:
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": query, "type": "artist", "limit": limite},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                artists = data.get("artists", {}).get("items", [])
                return [{
                    "nome": a["name"],
                    "generos": a.get("genres", []),
                    "popularidade": a.get("popularity", 0),
                    "url": a["external_urls"]["spotify"]
                } for a in artists]
        except Exception:
            pass
        return []


class TelegramBot:
    """Bot do Telegram para notificações."""

    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def enviar_mensagem(self, texto: str) -> bool:
        """Envia mensagem para o chat."""
        if not self.token or not self.chat_id or not _requests_ok:
            return False

        try:
            resp = requests.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": self.chat_id, "text": texto, "parse_mode": "HTML"},
                timeout=10
            )
            return resp.status_code == 200
        except Exception:
            return False

    def enviar_documento(self, caminho: str) -> bool:
        """Envia documento."""
        if not self.token or not self.chat_id or not _requests_ok:
            return False

        try:
            with open(caminho, "rb") as f:
                resp = requests.post(
                    f"{self.base_url}/sendDocument",
                    data={"chat_id": self.chat_id},
                    files={"document": f},
                    timeout=30
                )
            return resp.status_code == 200
        except Exception:
            return False

    def obter_updates(self) -> List[Dict]:
        """Obtém mensagens recebidas."""
        if not self.token or not _requests_ok:
            return []

        try:
            resp = requests.get(f"{self.base_url}/getUpdates", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("result", [])
        except Exception:
            pass
        return []


# ═══ GERENCIADOR DE APIs ═══
class APIManager:
    """Gerencia todas as integrações de API."""

    def __init__(self):
        self.twitter = TwitterAPI()
        self.github = GitHubAPI()
        self.weather = WeatherAPI()
        self.news = NewsAPI()
        self.spotify = SpotifyAPI()
        self.telegram = TelegramBot()

        print("[APIs] Gerenciador inicializado")
        self._verificar_apis()

    def _verificar_apis(self):
        """Verifica quais APIs estão configuradas."""
        apis = {
            "Twitter": bool(self.twitter.bearer_token),
            "GitHub": bool(self.github.token),
            "Weather": bool(self.weather.api_key),
            "News": bool(self.news.api_key),
            "Spotify": bool(self.spotify.client_id),
            "Telegram": bool(self.telegram.token)
        }
        for api, configurada in apis.items():
            status = "✅" if configurada else "❌"
            print(f"  {api}: {status}")

    def status(self) -> Dict:
        """Retorna status das APIs."""
        return {
            "twitter": bool(self.twitter.bearer_token),
            "github": bool(self.github.token),
            "weather": bool(self.weather.api_key),
            "news": bool(self.news.api_key),
            "spotify": bool(self.spotify.client_id),
            "telegram": bool(self.telegram.token)
        }


# ═══ INSTANCIA GLOBAL ═══
_api_instance = None


def get_api_manager() -> APIManager:
    """Retorna instância do gerenciador de APIs."""
    global _api_instance
    if _api_instance is None:
        _api_instance = APIManager()
    return _api_instance
