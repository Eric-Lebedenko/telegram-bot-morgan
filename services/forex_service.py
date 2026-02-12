from __future__ import annotations

import asyncio

from config import load_config
from services.http_client import HttpClient


class ForexService:
    def __init__(self, http: HttpClient | None = None) -> None:
        self.http = http or HttpClient()
        self.cfg = load_config()

    async def get_rates(self, base: str, symbols: list[str]) -> dict[str, str]:
        if not self.cfg.alphavantage_api_key:
            return {s: 'N/A' for s in symbols}
        rates: dict[str, str] = {}
        for symbol in symbols:
            try:
                data = await self.http.get_json(
                    'https://www.alphavantage.co/query',
                    params={
                        'function': 'CURRENCY_EXCHANGE_RATE',
                        'from_currency': base,
                        'to_currency': symbol,
                        'apikey': self.cfg.alphavantage_api_key,
                    },
                )
                rate = data.get('Realtime Currency Exchange Rate', {}).get('5. Exchange Rate')
                rates[symbol] = rate or 'N/A'
                await asyncio.sleep(0.25)
            except Exception:
                rates[symbol] = 'N/A'
        return rates

    async def get_pair_change(self, pair: str) -> dict[str, object]:
        if not self.cfg.alphavantage_api_key:
            return {}
        try:
            base, quote = pair.split('/')
        except Exception:
            return {}
        try:
            data = await self.http.get_json(
                'https://www.alphavantage.co/query',
                params={
                    'function': 'FX_DAILY',
                    'from_symbol': base,
                    'to_symbol': quote,
                    'apikey': self.cfg.alphavantage_api_key,
                },
            )
            series = data.get('Time Series FX (Daily)', {})
            if not series:
                return {}
            dates = sorted(series.keys(), reverse=True)
            if len(dates) < 2:
                return {}
            latest = series[dates[0]]
            prev = series[dates[1]]
            close = float(latest.get('4. close'))
            prev_close = float(prev.get('4. close'))
            change_pct = ((close - prev_close) / prev_close * 100.0) if prev_close else None
            return {
                'pair': pair,
                'rate': close,
                'change_pct': change_pct,
                'open': float(latest.get('1. open')),
                'high': float(latest.get('2. high')),
                'low': float(latest.get('3. low')),
                'prev_close': prev_close,
            }
        except Exception:
            return {}

    async def get_pairs_changes(self, pairs: list[str]) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for pair in pairs:
            item = await self.get_pair_change(pair)
            if item:
                results.append(item)
            await asyncio.sleep(0.25)
        return results
