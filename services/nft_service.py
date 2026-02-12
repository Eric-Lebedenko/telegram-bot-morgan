from __future__ import annotations

from config import load_config
from services.http_client import HttpClient


class NftService:
    def __init__(self, http: HttpClient | None = None) -> None:
        self.http = http or HttpClient()
        self.cfg = load_config()

    def _headers(self) -> dict[str, str]:
        if not self.cfg.opensea_api_key:
            return {}
        return {'X-API-KEY': self.cfg.opensea_api_key}

    async def get_floor_prices(self, collections: list[str]) -> dict[str, str]:
        if not self.cfg.opensea_api_key:
            return {c: 'N/A' for c in collections}
        result: dict[str, str] = {}
        for slug in collections:
            try:
                data = await self.http.get_json(
                    f'https://api.opensea.io/api/v2/collections/{slug}/stats',
                    headers=self._headers(),
                )
                stats = data.get('total', data)
                floor = stats.get('floor_price')
                result[slug] = f"{floor:.4f} ETH" if isinstance(floor, (int, float)) else 'N/A'
            except Exception:
                result[slug] = 'N/A'
        return result

    async def get_top_collections(self) -> list[str]:
        if not self.cfg.opensea_api_key:
            return []
        try:
            data = await self.http.get_json(
                'https://api.opensea.io/api/v2/collections',
                params={'limit': 5},
                headers=self._headers(),
            )
            items = data.get('collections', []) if isinstance(data, dict) else []
            return [item.get('name', 'N/A') for item in items][:5]
        except Exception:
            return []

    async def search_collection(self, query: str) -> list[str]:
        if not self.cfg.opensea_api_key:
            return [query]
        slug = query.strip().lower().replace(' ', '-')
        try:
            data = await self.http.get_json(
                f'https://api.opensea.io/api/v2/collection/{slug}',
                headers=self._headers(),
            )
            collection = data.get('collection', data)
            name = collection.get('name') or query
            return [name]
        except Exception:
            return [query]
