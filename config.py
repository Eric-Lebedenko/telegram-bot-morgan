from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    discord_bot_token: str
    telegram_webapp_url: str
    database_url: str

    finnhub_api_key: str
    alphavantage_api_key: str
    coinmarketcap_api_key: str
    coingecko_api_base: str
    newsapi_key: str
    tonapi_key: str
    opensea_api_key: str
    translate_api_url: str
    translate_api_key: str

    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_price_free: str
    stripe_price_pro: str
    stripe_price_elite: str

    crypto_payment_provider: str
    nowpayments_api_key: str

    admin_user_ids: set[int]
    discord_server_url: str


def _get_env(name: str, default: str = '') -> str:
    return os.getenv(name, default).strip()


def load_config() -> Config:
    admin_ids = _get_env('ADMIN_USER_IDS', '')
    admin_set: set[int] = set()
    if admin_ids:
        for raw in admin_ids.split(','):
            raw = raw.strip()
            if raw:
                try:
                    admin_set.add(int(raw))
                except ValueError:
                    pass

    return Config(
        telegram_bot_token=_get_env('TELEGRAM_BOT_TOKEN'),
        discord_bot_token=_get_env('DISCORD_BOT_TOKEN'),
        telegram_webapp_url=_get_env('TELEGRAM_WEBAPP_URL'),
        database_url=_get_env('DATABASE_URL', 'sqlite+aiosqlite:///./data/app.db'),

        finnhub_api_key=_get_env('FINNHUB_API_KEY'),
        alphavantage_api_key=_get_env('ALPHAVANTAGE_API_KEY'),
        coinmarketcap_api_key=_get_env('COINMARKETCAP_API_KEY'),
        coingecko_api_base=_get_env('COINGECKO_API_BASE', 'https://api.coingecko.com/api/v3'),
        newsapi_key=_get_env('NEWSAPI_KEY'),
        tonapi_key=_get_env('TONAPI_KEY'),
        opensea_api_key=_get_env('OPENSEA_API_KEY'),
        translate_api_url=_get_env('TRANSLATE_API_URL'),
        translate_api_key=_get_env('TRANSLATE_API_KEY'),

        stripe_secret_key=_get_env('STRIPE_SECRET_KEY'),
        stripe_webhook_secret=_get_env('STRIPE_WEBHOOK_SECRET'),
        stripe_price_free=_get_env('STRIPE_PRICE_FREE'),
        stripe_price_pro=_get_env('STRIPE_PRICE_PRO'),
        stripe_price_elite=_get_env('STRIPE_PRICE_ELITE'),

        crypto_payment_provider=_get_env('CRYPTO_PAYMENT_PROVIDER', 'nowpayments'),
        nowpayments_api_key=_get_env('NOWPAYMENTS_API_KEY'),

        admin_user_ids=admin_set,
        discord_server_url=_get_env('DISCORD_SERVER_URL'),
    )
