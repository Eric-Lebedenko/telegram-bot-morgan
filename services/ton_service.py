from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

from config import load_config
from services.http_client import HttpClient


class TonService:
    def __init__(self, http: HttpClient | None = None) -> None:
        self.http = http or HttpClient()
        self.cfg = load_config()

    def _headers(self) -> dict[str, str]:
        if not self.cfg.tonapi_key:
            return {}
        return {'Authorization': f'Bearer {self.cfg.tonapi_key}'}

    async def get_price(self) -> dict[str, str]:
        if not self.cfg.tonapi_key:
            return {'Price': 'N/A', 'Change 24h': 'N/A'}
        try:
            data = await self.http.get_json(
                'https://tonapi.io/v2/rates',
                params={'tokens': 'ton', 'currencies': 'usd'},
                headers=self._headers(),
            )
            price = None
            change = None
            rates = data.get('rates', {}) if isinstance(data, dict) else {}
            ton = rates.get('TON') or rates.get('ton') or {}
            prices = ton.get('prices', {}) if isinstance(ton, dict) else {}
            price = prices.get('USD') or prices.get('usd')
            change = ton.get('diff_24h') or ton.get('diff_24h_percent')
            return {
                'Price': f"${price:.4f}" if isinstance(price, (int, float)) else 'N/A',
                'Change 24h': f"{change:.2f}%" if isinstance(change, (int, float)) else 'N/A',
            }
        except Exception:
            return {'Price': 'N/A', 'Change 24h': 'N/A'}

    async def get_nft_collections(self) -> list[str]:
        if not self.cfg.tonapi_key:
            return []
        try:
            data = await self.http.get_json(
                'https://tonapi.io/v2/nfts/collections',
                params={'limit': 5},
                headers=self._headers(),
            )
            items = data.get('collections', []) if isinstance(data, dict) else []
            return [item.get('name', 'N/A') for item in items][:5]
        except Exception:
            return []

    async def lookup_wallet(self, address: str) -> dict[str, str]:
        if not self.cfg.tonapi_key:
            return {'Address': address, 'Balance': 'N/A', 'TX Count': 'N/A'}
        try:
            data = await self.http.get_json(
                f'https://tonapi.io/v2/accounts/{address}',
                headers=self._headers(),
            )
            balance_raw = data.get('balance')
            balance = 'N/A'
            if isinstance(balance_raw, (int, float)):
                balance = f"{balance_raw / 1_000_000_000:.4f} TON"
            return {
                'Address': address,
                'Balance': balance,
                'Status': str(data.get('status', 'N/A')),
            }
        except Exception:
            return {'Address': address, 'Balance': 'N/A', 'TX Count': 'N/A'}

    async def resolve_domain(self, domain: str) -> dict[str, object]:
        if not self.cfg.tonapi_key:
            return {}
        try:
            data = await self.http.get_json(
                f'https://tonapi.io/v2/dns/{quote(domain)}/resolve',
                headers=self._headers(),
            )
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    async def get_domain_info(self, domain: str) -> dict[str, object]:
        if not self.cfg.tonapi_key:
            return {}
        try:
            data = await self.http.get_json(
                f'https://tonapi.io/v2/dns/{quote(domain)}',
                headers=self._headers(),
            )
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    async def get_account_domains(self, address: str) -> list[str]:
        if not self.cfg.tonapi_key:
            return []
        try:
            data = await self.http.get_json(
                f'https://tonapi.io/v2/accounts/{quote(address)}/dns/backresolve',
                headers=self._headers(),
            )
            domains = data.get('domains', []) if isinstance(data, dict) else []
            return [str(d) for d in domains]
        except Exception:
            return []

    async def get_account_expiring_domains(self, address: str, period_days: int = 90) -> list[dict[str, object]]:
        if not self.cfg.tonapi_key:
            return []
        try:
            data = await self.http.get_json(
                f'https://tonapi.io/v2/accounts/{quote(address)}/dns/expiring',
                params={'period': period_days},
                headers=self._headers(),
            )
            items = data.get('items', []) if isinstance(data, dict) else []
            return items[:10]
        except Exception:
            return []

    async def get_account_nfts(self, address: str, limit: int = 10) -> list[dict[str, object]]:
        if not self.cfg.tonapi_key:
            return []
        try:
            data = await self.http.get_json(
                f'https://tonapi.io/v2/accounts/{quote(address)}/nfts',
                params={'limit': max(1, min(limit, 1000))},
                headers=self._headers(),
            )
            items = data.get('nft_items', []) if isinstance(data, dict) else []
            return items
        except Exception:
            return []

    async def get_jettons(self, limit: int = 10, offset: int = 0) -> list[dict[str, object]]:
        if not self.cfg.tonapi_key:
            return []
        try:
            data = await self.http.get_json(
                'https://tonapi.io/v2/jettons',
                params={'limit': max(1, min(limit, 1000)), 'offset': max(0, offset)},
                headers=self._headers(),
            )
            items = data.get('jettons', []) if isinstance(data, dict) else []
            return items
        except Exception:
            return []

    async def get_wallet_jettons(self, address: str) -> list[dict[str, object]]:
        if not self.cfg.tonapi_key:
            return []
        try:
            data = await self.http.get_json(
                f'https://tonapi.io/v2/accounts/{quote(address)}/jettons',
                headers=self._headers(),
            )
            balances = data.get('balances', []) if isinstance(data, dict) else []
            results: list[dict[str, object]] = []
            for bal in balances:
                jetton = bal.get('jetton') or {}
                symbol = jetton.get('symbol') or jetton.get('name') or 'JETTON'
                decimals = int(jetton.get('decimals') or 9)
                raw_balance = bal.get('balance')
                amount = None
                try:
                    amount = float(raw_balance) / (10 ** decimals)
                except Exception:
                    amount = None
                if amount is None or amount <= 0:
                    continue
                results.append({'symbol': symbol, 'amount': amount, 'name': jetton.get('name')})
            return results
        except Exception:
            return []

    @staticmethod
    def fmt_date(ts: object) -> str:
        if isinstance(ts, (int, float)):
            try:
                return datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d')
            except Exception:
                return 'N/A'
        return 'N/A'
