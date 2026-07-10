from ..base_module import BaseModule
from typing import Any, Dict, List
import requests
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


class NewsModule(BaseModule):
    def __init__(self):
        super().__init__(
            name="news",
            description="Buscar notícias, RSS feeds e últimas atualizações"
        )
        self._feeds = [
            "https://g1.globo.com/rss/g1/",
            "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
            "https://rss.uol.com.br/feed/noticias.xml"
        ]

    def _load_resources(self):
        logger.info("Carregando recursos de notícias...")

        self._metadata = {
            "version": "1.0",
            "capabilities": [
                "get_headlines",
                "search_news",
                "get_feed",
                "get_tech_news"
            ]
        }

    def _unload_resources(self):
        logger.info("Recursos de notícias liberados")

    def execute(self, action: str, **kwargs) -> Any:
        actions = {
            "headlines": self._get_headlines,
            "search": self._search_news,
            "feed": self._get_feed,
            "tech": self._get_tech_news
        }

        if action not in actions:
            raise ValueError(f"Ação não suportada: {action}")

        return actions[action](**kwargs)

    def _parse_rss(self, url: str, limit: int = 10) -> List[Dict]:
        try:
            response = requests.get(url, timeout=10)
            root = ET.fromstring(response.content)

            items = []
            for item in root.findall('.//item')[:limit]:
                title = item.find('title')
                link = item.find('link')
                description = item.find('description')
                pub_date = item.find('pubDate')

                items.append({
                    "title": title.text if title is not None else "",
                    "link": link.text if link is not None else "",
                    "description": description.text[:200] if description is not None else "",
                    "date": pub_date.text if pub_date is not None else ""
                })

            return items
        except Exception as e:
            logger.error(f"Erro ao parsear RSS {url}: {e}")
            return []

    def _get_headlines(self, limit: int = 10, **kwargs) -> List[Dict]:
        all_items = []
        for feed in self._feeds:
            items = self._parse_rss(feed, limit=5)
            all_items.extend(items)

        all_items.sort(key=lambda x: x.get("date", ""), reverse=True)
        return all_items[:limit]

    def _search_news(self, query: str, **kwargs) -> List[Dict]:
        headlines = self._get_headlines(limit=20)

        results = []
        for item in headlines:
            if query.lower() in item.get("title", "").lower() or query.lower() in item.get("description", "").lower():
                results.append(item)

        return results

    def _get_feed(self, feed_url: str = None, **kwargs) -> List[Dict]:
        url = feed_url or self._feeds[0]
        return self._parse_rss(url, limit=15)

    def _get_tech_news(self, **kwargs) -> List[Dict]:
        tech_feeds = [
            "https://tecnoblog.net/feed/",
            "https://tecmundo.com.br/rss",
            "https://olhardigital.com.br/feed"
        ]

        all_items = []
        for feed in tech_feeds:
            items = self._parse_rss(feed, limit=5)
            all_items.extend(items)

        return all_items[:10]
