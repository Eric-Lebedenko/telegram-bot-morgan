from __future__ import annotations

from config import load_config
from services.http_client import HttpClient


CMC_BASE = 'https://pro-api.coinmarketcap.com'

SYMBOL_MAP = {
    'bitcoin': 'BTC',
    'btc': 'BTC',
    'ethereum': 'ETH',
    'eth': 'ETH',
    'solana': 'SOL',
    'sol': 'SOL',
    'ton': 'TON',
    'toncoin': 'TON',
}


class CryptoService:
    def __init__(self, http: HttpClient | None = None) -> None:
        self.http = http or HttpClient()
        self.cfg = load_config()

    def _to_symbol(self, value: str) -> str:
        key = (value or '').lower().strip()
        return SYMBOL_MAP.get(key, value.upper())

    async def get_prices(self, ids: list[str]) -> dict[str, str]:
        if not self.cfg.coinmarketcap_api_key:
            return {i: 'N/A' for i in ids}
        symbols = [self._to_symbol(i) for i in ids]
        try:
            data = await self.http.get_json(
                f"{CMC_BASE}/v1/cryptocurrency/quotes/latest",
                params={'symbol': ','.join(symbols)},
                headers={'X-CMC_PRO_API_KEY': self.cfg.coinmarketcap_api_key},
            )
            result = {}
            for original, symbol in zip(ids, symbols):
                item = data.get('data', {}).get(symbol, {})
                price = item.get('quote', {}).get('USD', {}).get('price')
                result[original] = f"${price:.2f}" if isinstance(price, (int, float)) else 'N/A'
            return result
        except Exception:
            return {i: 'N/A' for i in ids}

    async def get_quotes(self, symbols: list[str]) -> dict[str, dict[str, float | None]]:
        if not self.cfg.coinmarketcap_api_key:
            return {}
        norm = [self._to_symbol(s) for s in symbols]
        try:
            data = await self.http.get_json(
                f"{CMC_BASE}/v1/cryptocurrency/quotes/latest",
                params={'symbol': ','.join(norm), 'convert': 'USD'},
                headers={'X-CMC_PRO_API_KEY': self.cfg.coinmarketcap_api_key},
            )
            result: dict[str, dict[str, float | None]] = {}
            for sym in norm:
                item = data.get('data', {}).get(sym, {})
                quote = item.get('quote', {}).get('USD', {})
                result[sym] = {
                    'price': quote.get('price'),
                    'change_24h': quote.get('percent_change_24h'),
                    'market_cap': quote.get('market_cap'),
                    'volume_24h': quote.get('volume_24h'),
                }
            return result
        except Exception:
            return {}

    async def get_asset(self, symbol: str) -> dict[str, float | None] | None:
        data = await self.get_quotes([symbol])
        return data.get(self._to_symbol(symbol))

    async def get_top_assets(self, limit: int = 100) -> list[dict[str, object]]:
        if not self.cfg.coinmarketcap_api_key:
            return []
        try:
            data = await self.http.get_json(
                f"{CMC_BASE}/v1/cryptocurrency/listings/latest",
                params={'start': 1, 'limit': limit, 'convert': 'USD'},
                headers={'X-CMC_PRO_API_KEY': self.cfg.coinmarketcap_api_key},
            )
            items = data.get('data', [])
            result: list[dict[str, object]] = []
            for item in items:
                quote = item.get('quote', {}).get('USD', {})
                result.append({
                    'rank': item.get('cmc_rank'),
                    'symbol': item.get('symbol'),
                    'name': item.get('name'),
                    'price': quote.get('price'),
                    'change_24h': quote.get('percent_change_24h'),
                    'market_cap': quote.get('market_cap'),
                    'volume_24h': quote.get('volume_24h'),
                })
            return result
        except Exception:
            return []

    async def get_dominance(self) -> dict[str, str]:
        if not self.cfg.coinmarketcap_api_key:
            return {'BTC': 'N/A', 'ETH': 'N/A'}
        try:
            data = await self.http.get_json(
                f"{CMC_BASE}/v1/global-metrics/quotes/latest",
                headers={'X-CMC_PRO_API_KEY': self.cfg.coinmarketcap_api_key},
            )
            metrics = data.get('data', {})
            btc = metrics.get('btc_dominance')
            eth = metrics.get('eth_dominance')
            return {
                'BTC': f"{btc:.2f}%" if isinstance(btc, (int, float)) else 'N/A',
                'ETH': f"{eth:.2f}%" if isinstance(eth, (int, float)) else 'N/A',
            }
        except Exception:
            return {'BTC': 'N/A', 'ETH': 'N/A'}

    async def get_onchain_summary(self, asset: str) -> dict[str, str]:
        return {'Status': 'On-chain provider not configured'}
