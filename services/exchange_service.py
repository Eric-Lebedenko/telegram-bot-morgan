from __future__ import annotations

import asyncio

try:
    import ccxt  # type: ignore
except Exception:
    ccxt = None


class ExchangeService:
    async def fetch_balances(self, provider: str, api_key: str, api_secret: str, passphrase: str | None = None) -> list[dict[str, object]]:
        if ccxt is None:
            raise RuntimeError('ccxt_missing')
        provider = provider.lower().strip()
        if provider not in ('binance', 'bybit', 'okx'):
            raise ValueError('unsupported')

        def _run() -> dict:
            exchange_cls = getattr(ccxt, provider)
            params = {'apiKey': api_key, 'secret': api_secret}
            if passphrase:
                params['password'] = passphrase
            exchange = exchange_cls(params)
            exchange.load_markets()
            return exchange.fetch_balance()

        data = await asyncio.to_thread(_run)
        totals = data.get('total', {}) if isinstance(data, dict) else {}
        results = []
        for symbol, amount in totals.items():
            try:
                amount_f = float(amount)
            except Exception:
                continue
            if amount_f > 0:
                results.append({'symbol': symbol, 'amount': amount_f})
        return results
