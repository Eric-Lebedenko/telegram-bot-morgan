from __future__ import annotations

from datetime import datetime, timedelta
import asyncio
import time

from config import load_config
from services.http_client import HttpClient


class StocksService:
    def __init__(self, http: HttpClient | None = None) -> None:
        self.http = http or HttpClient()
        self.cfg = load_config()

    async def get_price(self, symbol: str) -> dict[str, str]:
        if not self.cfg.finnhub_api_key:
            return {'symbol': symbol, 'price': 'N/A', 'change': 'N/A'}
        try:
            data = await self.http.get_json(
                'https://finnhub.io/api/v1/quote',
                params={'symbol': symbol, 'token': self.cfg.finnhub_api_key},
            )
            price = data.get('c')
            change = data.get('d')
            return {
                'symbol': symbol,
                'price': f"{price:.2f}" if isinstance(price, (int, float)) else 'N/A',
                'change': f"{change:.2f}" if isinstance(change, (int, float)) else 'N/A',
            }
        except Exception:
            return {'symbol': symbol, 'price': 'N/A', 'change': 'N/A'}

    async def get_quote_details(self, symbol: str) -> dict[str, object]:
        if not self.cfg.finnhub_api_key:
            return {}
        try:
            data = await self.http.get_json(
                'https://finnhub.io/api/v1/quote',
                params={'symbol': symbol, 'token': self.cfg.finnhub_api_key},
            )
            price = data.get('c')
            change = data.get('d')
            change_pct = data.get('dp')
            prev_close = data.get('pc')
            volume = await self._get_daily_volume(symbol)
            return {
                'symbol': symbol,
                'price': price,
                'change': change,
                'change_pct': change_pct,
                'prev_close': prev_close,
                'volume': volume,
            }
        except Exception:
            return {}

    async def get_quotes_details(self, symbols: list[str]) -> list[dict[str, object]]:
        tasks = [self.get_quote_details(sym) for sym in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        items: list[dict[str, object]] = []
        for sym, result in zip(symbols, results, strict=False):
            if isinstance(result, dict) and result:
                items.append(result)
            else:
                items.append({'symbol': sym})
        return items

    async def _get_daily_volume(self, symbol: str) -> float | None:
        try:
            now = int(time.time())
            start = now - 86400 * 7
            data = await self.http.get_json(
                'https://finnhub.io/api/v1/stock/candle',
                params={
                    'symbol': symbol,
                    'resolution': 'D',
                    'from': start,
                    'to': now,
                    'token': self.cfg.finnhub_api_key,
                },
            )
            if data.get('s') != 'ok':
                return None
            vols = data.get('v', [])
            if vols:
                return float(vols[-1])
            return None
        except Exception:
            return None

    async def get_quotes(self, symbols: list[str]) -> dict[str, dict[str, str]]:
        if not symbols:
            return {}
        tasks = [self.get_price(sym) for sym in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        quotes: dict[str, dict[str, str]] = {}
        for sym, result in zip(symbols, results, strict=False):
            if isinstance(result, dict):
                quotes[sym] = result
            else:
                quotes[sym] = {'symbol': sym, 'price': 'N/A', 'change': 'N/A'}
        return quotes

    async def get_fundamentals(self, symbol: str) -> dict[str, str]:
        if not self.cfg.finnhub_api_key:
            return {'Market Cap': 'N/A', 'PE Ratio': 'N/A', 'EPS': 'N/A'}
        try:
            data = await self.http.get_json(
                'https://finnhub.io/api/v1/stock/metric',
                params={'symbol': symbol, 'metric': 'all', 'token': self.cfg.finnhub_api_key},
            )
            metric = data.get('metric', {})
            return {
                'Market Cap (M)': str(metric.get('marketCapitalization', 'N/A')),
                'PE (TTM)': str(metric.get('peNormalizedAnnual', 'N/A')),
                'EPS (TTM)': str(metric.get('epsTTM', 'N/A')),
            }
        except Exception:
            return {'Market Cap': 'N/A', 'PE Ratio': 'N/A', 'EPS': 'N/A'}

    async def get_ratios(self, symbol: str) -> dict[str, str]:
        if not self.cfg.finnhub_api_key:
            return {'P/E': 'N/A', 'P/B': 'N/A', 'ROE': 'N/A'}
        try:
            data = await self.http.get_json(
                'https://finnhub.io/api/v1/stock/metric',
                params={'symbol': symbol, 'metric': 'all', 'token': self.cfg.finnhub_api_key},
            )
            metric = data.get('metric', {})
            return {
                'P/E (TTM)': str(metric.get('peBasicExclExtraTTM', 'N/A')),
                'P/B (Annual)': str(metric.get('pbAnnual', 'N/A')),
                'ROE (TTM)': str(metric.get('roeTTM', 'N/A')),
            }
        except Exception:
            return {'P/E': 'N/A', 'P/B': 'N/A', 'ROE': 'N/A'}

    async def get_metrics(self, symbol: str) -> dict[str, object]:
        if not self.cfg.finnhub_api_key:
            return {}
        try:
            data = await self.http.get_json(
                'https://finnhub.io/api/v1/stock/metric',
                params={'symbol': symbol, 'metric': 'all', 'token': self.cfg.finnhub_api_key},
            )
            return data.get('metric', {}) or {}
        except Exception:
            return {}

    async def get_earnings(self, symbol: str) -> list[dict[str, str]]:
        if not self.cfg.finnhub_api_key:
            return []
        try:
            now = datetime.utcnow().date()
            start = (now - timedelta(days=365)).isoformat()
            end = (now + timedelta(days=365)).isoformat()
            data = await self.http.get_json(
                'https://finnhub.io/api/v1/calendar/earnings',
                params={'symbol': symbol, 'from': start, 'to': end, 'token': self.cfg.finnhub_api_key},
            )
            items = data.get('earningsCalendar', [])
            return [
                {
                    'date': i.get('date', 'N/A'),
                    'eps': str(i.get('epsActual') or i.get('epsEstimate') or 'N/A'),
                }
                for i in items[:5]
            ]
        except Exception:
            return []

    async def get_dividends(self, symbol: str) -> list[dict[str, str]]:
        if not self.cfg.finnhub_api_key:
            return []
        try:
            now = datetime.utcnow().date()
            start = (now - timedelta(days=365)).isoformat()
            end = (now + timedelta(days=365)).isoformat()
            data = await self.http.get_json(
                'https://finnhub.io/api/v1/stock/dividend',
                params={'symbol': symbol, 'from': start, 'to': end, 'token': self.cfg.finnhub_api_key},
            )
            return [
                {
                    'date': i.get('date', 'N/A'),
                    'amount': str(i.get('amount', 'N/A')),
                }
                for i in data[:5]
            ]
        except Exception:
            return []

    async def get_top_etfs(self) -> list[str]:
        return ['SPY', 'QQQ', 'VTI', 'IWM', 'DIA']

    async def get_social_sentiment(self, symbol: str) -> dict[str, dict[str, object]]:
        if not self.cfg.finnhub_api_key:
            return {}
        try:
            now = datetime.utcnow().date()
            start = (now - timedelta(days=7)).isoformat()
            end = now.isoformat()
            data = await self.http.get_json(
                'https://finnhub.io/api/v1/stock/social-sentiment',
                params={'symbol': symbol, 'from': start, 'to': end, 'token': self.cfg.finnhub_api_key},
            )
            return {
                'reddit': self._summarize_sentiment(data.get('reddit') or []),
                'twitter': self._summarize_sentiment(data.get('twitter') or []),
            }
        except Exception:
            return {}

    def _summarize_sentiment(self, items: list[dict[str, object]]) -> dict[str, object]:
        if not items:
            return {
                'mentions': 0,
                'score': None,
                'positive': None,
                'negative': None,
            }
        total_score = 0.0
        total_mentions = 0
        total_pos = 0
        total_neg = 0
        for item in items:
            total_score += float(item.get('score') or 0)
            total_mentions += int(item.get('mention') or 0)
            total_pos += int(item.get('positiveMention') or 0)
            total_neg += int(item.get('negativeMention') or 0)
        avg_score = total_score / max(1, len(items))
        return {
            'mentions': total_mentions,
            'score': avg_score,
            'positive': total_pos,
            'negative': total_neg,
        }
