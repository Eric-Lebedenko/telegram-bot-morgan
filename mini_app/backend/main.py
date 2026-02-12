from __future__ import annotations

import hashlib
import hmac
import json
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import load_config
from database import init_db
from core.permissions import UserContext
from services.payment_service import PaymentService
from services.portfolio_service import PortfolioService
from services.crypto_service import CryptoService
from services.stocks_service import StocksService
from services.ton_service import TonService
from services.nft_service import NftService
from services.education_service import EducationService
from services.forex_service import ForexService
from services.news_service import NewsService
from services.user_service import UserService

app = FastAPI(title='Investment Mini App API')

cfg = load_config()
portfolio = PortfolioService()
crypto = CryptoService()
stocks = StocksService()
ton = TonService()
nft = NftService()
education = EducationService()
payments = PaymentService()
forex = ForexService()
news = NewsService()
users = UserService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


class AuthUser(BaseModel):
    user_id: str
    username: str | None
    language: str | None = None


def _verify_init_data(init_data: str, token: str) -> bool:
    if not init_data:
        return False
    pairs = [kv for kv in init_data.split('&') if kv]
    data = {}
    received_hash = ''
    for kv in pairs:
        key, value = kv.split('=', 1)
        if key == 'hash':
            received_hash = value
        else:
            data[key] = value
    check_string = '\n'.join([f"{k}={data[k]}" for k in sorted(data.keys())])
    secret_key = hashlib.sha256(token.encode()).digest()
    computed = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, received_hash)


def telegram_auth(telegram_init_data: str = Header(default='', alias='Telegram-Init-Data')) -> AuthUser:
    if not _verify_init_data(telegram_init_data, cfg.telegram_bot_token):
        raise HTTPException(status_code=401, detail='Invalid Telegram auth')
    params = parse_qs(telegram_init_data, keep_blank_values=True)
    raw_user = params.get('user', [None])[0]
    if raw_user:
        try:
            user_obj = json.loads(raw_user)
            return AuthUser(
                user_id=str(user_obj.get('id', 'telegram_user')),
                username=user_obj.get('username'),
                language=user_obj.get('language_code'),
            )
        except json.JSONDecodeError:
            pass
    return AuthUser(user_id='telegram_user', username=None, language=None)


async def _get_ctx(user: AuthUser) -> UserContext:
    is_admin = user.user_id in cfg.admin_user_ids
    return await users.get_or_create_user(
        'telegram',
        user.user_id,
        user.username,
        is_admin,
        user.language,
    )


def _sort_quotes(items: list[dict[str, object]], sort: str) -> list[dict[str, object]]:
    if sort == 'losers':
        return sorted(items, key=lambda x: (x.get('change_pct') or 0))
    if sort == 'volume':
        return sorted(items, key=lambda x: -(x.get('volume') or 0))
    if sort == 'popular':
        return items
    return sorted(items, key=lambda x: -(x.get('change_pct') or 0))


@app.on_event('startup')
async def _startup() -> None:
    await init_db()


@app.get('/health')
async def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.get('/api/dashboard')
async def dashboard(user: AuthUser = Depends(telegram_auth)) -> dict:
    prices = await crypto.get_prices(['bitcoin', 'ethereum', 'solana'])
    stock_symbols = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL']
    stock_quotes = await stocks.get_quotes_details(stock_symbols)
    crypto_top = await crypto.get_top_assets(5)
    return {
        'user': user.model_dump(),
        'prices': prices,
        'stocks_top': stock_quotes,
        'crypto_top': crypto_top,
        'highlights': [
            {'label': 'BTC Dominance', 'value': 'N/A'},
            {'label': 'Fear & Greed', 'value': 'N/A'},
        ],
    }


@app.get('/api/markets/stocks/top')
async def market_stocks_top(sort: str = 'gainers', user: AuthUser = Depends(telegram_auth)) -> dict:
    symbols = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA', 'JPM', 'V', 'UNH']
    items = await stocks.get_quotes_details(symbols)
    return {'items': _sort_quotes(items, sort)}


@app.get('/api/markets/etfs/top')
async def market_etfs_top(sort: str = 'gainers', user: AuthUser = Depends(telegram_auth)) -> dict:
    symbols = ['SPY', 'QQQ', 'VTI', 'IWM', 'DIA', 'XLK', 'XLF', 'XLV']
    items = await stocks.get_quotes_details(symbols)
    return {'items': _sort_quotes(items, sort)}


@app.get('/api/markets/forex/top')
async def market_forex_top(sort: str = 'gainers', user: AuthUser = Depends(telegram_auth)) -> dict:
    pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD']
    items = await forex.get_pairs_changes(pairs)
    if sort == 'losers':
        items = sorted(items, key=lambda x: (x.get('change_pct') or 0))
    else:
        items = sorted(items, key=lambda x: -(x.get('change_pct') or 0))
    return {'items': items}


@app.get('/api/crypto/prices')
async def crypto_prices(user: AuthUser = Depends(telegram_auth)) -> dict:
    prices = await crypto.get_prices(['bitcoin', 'ethereum', 'solana'])
    return {'prices': prices}


@app.get('/api/crypto/top')
async def crypto_top(limit: int = 10, user: AuthUser = Depends(telegram_auth)) -> dict:
    items = await crypto.get_top_assets(limit)
    return {'items': items}


@app.get('/api/crypto/asset/{symbol}')
async def crypto_asset(symbol: str, user: AuthUser = Depends(telegram_auth)) -> dict:
    item = await crypto.get_asset(symbol.upper())
    return {'symbol': symbol.upper(), 'quote': item}


@app.get('/api/ton/price')
async def ton_price(user: AuthUser = Depends(telegram_auth)) -> dict:
    data = await ton.get_price()
    return {'price': data}


@app.get('/api/ton/projects')
async def ton_projects(limit: int = 8, offset: int = 0, user: AuthUser = Depends(telegram_auth)) -> dict:
    items = await ton.get_jettons(limit=limit, offset=offset)
    return {'items': items}


@app.get('/api/ton/nft/collections')
async def ton_nft_collections(user: AuthUser = Depends(telegram_auth)) -> dict:
    items = await ton.get_nft_collections()
    return {'collections': items}


@app.get('/api/ton/wallet/{address}')
async def ton_wallet(address: str, user: AuthUser = Depends(telegram_auth)) -> dict:
    data = await ton.lookup_wallet(address)
    return data


@app.get('/api/nft/collections')
async def nft_collections(user: AuthUser = Depends(telegram_auth)) -> dict:
    collections = await nft.get_top_collections()
    return {'collections': collections}


@app.get('/api/nft/floors')
async def nft_floors(user: AuthUser = Depends(telegram_auth)) -> dict:
    floors = await nft.get_floor_prices(['azuki', 'bored-ape-yacht-club', 'pudgy-penguins', 'doodles-official'])
    return {'floors': floors}


@app.get('/api/portfolio')
async def portfolio_overview(user: AuthUser = Depends(telegram_auth)) -> dict:
    ctx = await _get_ctx(user)
    allocation = await portfolio.get_allocation(ctx)
    return {'allocation': allocation}


@app.get('/api/portfolio/items')
async def portfolio_items(user: AuthUser = Depends(telegram_auth)) -> dict:
    ctx = await _get_ctx(user)
    items = await portfolio.list_assets(ctx)
    return {'items': items[:30]}


@app.get('/api/education/lessons')
async def education_lessons(user: AuthUser = Depends(telegram_auth)) -> dict:
    lessons = await education.get_lessons(user.language or 'ru')
    titles = [str(l.get('title')) for l in lessons]
    return {'lessons': titles}


@app.get('/api/education/glossary')
async def education_glossary(user: AuthUser = Depends(telegram_auth)) -> dict:
    items = await education.get_glossary(user.language or 'ru')
    return {'glossary': items}


@app.get('/api/news/headlines')
async def news_headlines(user: AuthUser = Depends(telegram_auth)) -> dict:
    items = await news.get_headlines()
    return {'items': items[:12]}


@app.get('/api/news/project/{query}')
async def news_project(query: str, user: AuthUser = Depends(telegram_auth)) -> dict:
    items = await news.get_project_news(query)
    return {'items': items[:12]}


@app.get('/api/user/profile')
async def user_profile(user: AuthUser = Depends(telegram_auth)) -> dict:
    ctx = await _get_ctx(user)
    return {
        'user_id': ctx.user_id,
        'username': ctx.username,
        'tier': ctx.tier,
        'language': ctx.language,
        'badge': ctx.badge,
    }


@app.post('/api/payments/stripe/checkout/{tier}')
async def stripe_checkout(tier: str, user: AuthUser = Depends(telegram_auth)) -> dict:
    ctx = await _get_ctx(user)
    url = await payments.create_checkout_link(ctx, tier)
    return {'url': url}


@app.post('/api/payments/stripe/webhook')
async def stripe_webhook(request: Request, stripe_signature: str = Header(default='', alias='Stripe-Signature')) -> dict:
    payload = await request.body()
    return await payments.handle_stripe_webhook(payload, stripe_signature)


@app.post('/api/payments/crypto/webhook')
async def crypto_webhook() -> dict:
    return {'status': 'ok'}
