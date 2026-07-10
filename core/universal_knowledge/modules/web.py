from ..base_module import BaseModule
from typing import Any, Dict, List
import webbrowser
import requests
import logging

logger = logging.getLogger(__name__)


class WebModule(BaseModule):
    def __init__(self):
        super().__init__(
            name="web",
            description="Navegação web, busca, downloads e automação de navegador"
        )
        self._session = None

    def _load_resources(self):
        logger.info("Carregando recursos web...")
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JARVIS/1.0"
        })

        self._metadata = {
            "version": "1.0",
            "capabilities": [
                "open_url",
                "search",
                "fetch_page",
                "download",
                "get_weather"
            ]
        }

    def _unload_resources(self):
        self._session = None
        logger.info("Recursos web liberados")

    def execute(self, action: str, **kwargs) -> Any:
        actions = {
            "open": self._open_url,
            "search": self._search,
            "fetch": self._fetch_page,
            "download": self._download,
            "weather": self._get_weather
        }

        if action not in actions:
            raise ValueError(f"Ação não suportada: {action}")

        return actions[action](**kwargs)

    def _open_url(self, url: str, **kwargs) -> bool:
        webbrowser.open(url)
        return True

    def _search(self, query: str, **kwargs) -> List[Dict]:
        # TODO: Implementar com API de busca real
        return [{"title": "Resultado 1", "url": "https://example.com"}]

    def _fetch_page(self, url: str, **kwargs) -> str:
        response = self._session.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def _download(self, url: str, output_path: str, **kwargs) -> bool:
        response = self._session.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True

    def _get_weather(self, city: str = "São Paulo", **kwargs) -> Dict:
        try:
            response = self._session.get(
                f"https://wttr.in/{city}?format=j1",
                timeout=10
            )
            data = response.json()

            current = data.get("current_condition", [{}])[0]
            return {
                "city": city,
                "temp_c": current.get("temp_C"),
                "description": current.get("weatherDesc", [{}])[0].get("value"),
                "humidity": current.get("humidity"),
                "wind_kmph": current.get("windspeedKmph")
            }
        except Exception as e:
            logger.error(f"Erro ao buscar clima: {e}")
            return {"error": str(e)}
