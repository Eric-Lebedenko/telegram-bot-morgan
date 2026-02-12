from __future__ import annotations

from datetime import datetime, timedelta

from config import load_config
from services.http_client import HttpClient


class NewsService:
    def __init__(self, http: HttpClient | None = None) -> None:
        self.http = http or HttpClient()
        self.cfg = load_config()

    async def get_headlines(self) -> list[dict[str, object]]:
        if self.cfg.finnhub_api_key:
            try:
                data = await self.http.get_json(
                    'https://finnhub.io/api/v1/news',
                    params={'category': 'general', 'token': self.cfg.finnhub_api_key},
                )
                items = []
                for article in data[:30]:
                    items.append({
                        'title': article.get('headline', 'N/A'),
                        'url': article.get('url', ''),
                        'source': article.get('source', 'N/A'),
                        'summary': article.get('summary', ''),
                        'datetime': article.get('datetime'),
                    })
                return items
            except Exception:
                return []
        if self.cfg.newsapi_key:
            data = await self.http.get_json(
                'https://newsapi.org/v2/top-headlines',
                params={'category': 'business', 'language': 'en', 'apiKey': self.cfg.newsapi_key},
            )
            items = []
            for article in data.get('articles', [])[:30]:
                items.append({
                    'title': article.get('title', 'N/A'),
                    'url': article.get('url', ''),
                    'source': (article.get('source') or {}).get('name', 'N/A'),
                    'summary': article.get('description', ''),
                    'datetime': article.get('publishedAt'),
                })
            return items
        return []

    async def get_project_news(self, query: str) -> list[dict[str, object]]:
        if self.cfg.finnhub_api_key:
            symbol = query.upper()
            end = datetime.utcnow().date()
            start = end - timedelta(days=7)
            try:
                data = await self.http.get_json(
                    'https://finnhub.io/api/v1/company-news',
                    params={
                        'symbol': symbol,
                        'from': start.isoformat(),
                        'to': end.isoformat(),
                        'token': self.cfg.finnhub_api_key,
                    },
                )
                if data:
                    return [
                        {
                            'title': article.get('headline', 'N/A'),
                            'url': article.get('url', ''),
                            'source': article.get('source', 'N/A'),
                            'summary': article.get('summary', ''),
                            'datetime': article.get('datetime'),
                        }
                        for article in data[:30]
                    ]
            except Exception:
                pass
            try:
                data = await self.http.get_json(
                    'https://finnhub.io/api/v1/news',
                    params={'category': 'general', 'token': self.cfg.finnhub_api_key},
                )
                return [
                    {
                        'title': a.get('headline', 'N/A'),
                        'url': a.get('url', ''),
                        'source': a.get('source', 'N/A'),
                        'summary': a.get('summary', ''),
                        'datetime': a.get('datetime'),
                    }
                    for a in data
                    if query.lower() in (a.get('headline', '').lower())
                ][:30]
            except Exception:
                return []
        if self.cfg.newsapi_key:
            data = await self.http.get_json(
                'https://newsapi.org/v2/everything',
                params={'q': query, 'language': 'en', 'apiKey': self.cfg.newsapi_key},
            )
            items = []
            for article in data.get('articles', [])[:30]:
                items.append({
                    'title': article.get('title', 'N/A'),
                    'url': article.get('url', ''),
                    'source': (article.get('source') or {}).get('name', 'N/A'),
                    'summary': article.get('description', ''),
                    'datetime': article.get('publishedAt'),
                })
            return items
        return []
