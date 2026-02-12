# Unified Telegram + Discord Investment Bot

## Setup Guide
1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in tokens and API keys.
3. Initialize the database:

```bash
python -c "import asyncio; from database import init_db; asyncio.run(init_db())"
```

4. Run the bots:

```bash
python main.py --telegram
python main.py --discord
```

## Data Providers
- Stocks/Fundamentals/Earnings/Dividends: Finnhub
- Forex: Alpha Vantage
- Crypto: CoinMarketCap
- TON: tonapi.io
- NFT: OpenSea
- News: Finnhub (or NewsAPI fallback)

## Mini App Setup
Backend:

```bash
uvicorn mini_app.backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd mini_app/frontend
npm install
npm run dev
```

Set `VITE_API_BASE` to your backend URL.

## Telegram Commands
- `/start` — main menu
- `/menu` — main menu
- `/dashboard` — quick market overview
- `/price` — stock search menu
- `/crypto` — crypto menu
- `/valuation` — Shiller/Graham valuation (asks for ticker)
- `/help` — onboarding
- `/faq` — glossary

## Vercel Frontend Deploy
1. Push this repo to GitHub.
2. In Vercel: **New Project → Import Git Repository**.
3. Root Directory: `mini_app/frontend`.
4. Build Command: `npm run build`.
5. Output Directory: `dist`.
6. Env var: `VITE_API_BASE=https://YOUR_BACKEND_DOMAIN`.
7. Deploy and copy the URL into `TELEGRAM_WEBAPP_URL` (and BotFather Mini App URL).

## Deployment Instructions
- Deploy bot processes as system services (systemd, Docker, or PM2).
- Host FastAPI with Uvicorn behind a reverse proxy (Nginx) and TLS.
- Build frontend with `npm run build` and serve via CDN or static hosting.
- Set the Telegram Web App URL in BotFather to the frontend URL.

## Payments
- Create Stripe products/prices for Pro and Elite, then set `STRIPE_PRICE_PRO` and `STRIPE_PRICE_ELITE`.
- Configure the webhook endpoint at `/api/payments/stripe/webhook` and set `STRIPE_WEBHOOK_SECRET`.
- For crypto payments, integrate your provider and point its webhook to `/api/payments/crypto/webhook`.

## Add New Module
1. Create a service in `services/` with async methods.
2. Add menu entries in `core/router.py` and map actions.
3. Implement handler in router and update permissions in `core/permissions.py`.
4. Add any API endpoints to `mini_app/backend/main.py` and frontend cards.
