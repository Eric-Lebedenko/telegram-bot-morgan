from __future__ import annotations

import asyncio
from typing import Any

import stripe

from config import load_config
from core.permissions import UserContext, normalize_tier
from database import get_db, fetchone


class PaymentService:
    def __init__(self) -> None:
        self.cfg = load_config()
        stripe.api_key = self.cfg.stripe_secret_key

    async def get_subscription_status(self, user: UserContext) -> str:
        async with get_db() as db:
            row = await fetchone(
                db,
                'SELECT tier, status, ends_at FROM subscriptions WHERE user_id = ? ORDER BY id DESC LIMIT 1',
                (user.user_id,),
            )
        if not row:
            return f"Current tier: {user.tier.upper()} (no active subscription)"
        ends = row['ends_at'] or 'N/A'
        return f"Tier: {row['tier'].upper()} | Status: {row['status']} | Ends: {ends}"

    async def get_manage_link(self, user: UserContext) -> str:
        if not self.cfg.stripe_secret_key:
            return 'Stripe is not configured.'
        async with get_db() as db:
            row = await fetchone(db, 'SELECT stripe_customer_id FROM users WHERE id = ?', (user.user_id,))
        customer_id = row['stripe_customer_id'] if row else None
        if not customer_id:
            return 'No billing profile yet. Upgrade to create one.'
        return await asyncio.to_thread(self._create_billing_portal, customer_id)

    async def create_checkout_link(self, user: UserContext, tier: str) -> str:
        if not self.cfg.stripe_secret_key:
            return 'Stripe is not configured.'
        price_id = self._price_id_for_tier(tier)
        if not price_id:
            return 'Stripe price ID missing for this tier.'
        async with get_db() as db:
            row = await fetchone(db, 'SELECT stripe_customer_id FROM users WHERE id = ?', (user.user_id,))
        customer_id = row['stripe_customer_id'] if row else None
        return await asyncio.to_thread(self._create_checkout_session, user, tier, price_id, customer_id)

    async def handle_stripe_webhook(self, payload: bytes, sig_header: str) -> dict[str, Any]:
        if not self.cfg.stripe_webhook_secret:
            return {'status': 'ignored'}
        event = stripe.Webhook.construct_event(payload, sig_header, self.cfg.stripe_webhook_secret)
        event_type = event['type']
        data = event['data']['object']

        if event_type == 'checkout.session.completed':
            await self._handle_checkout_completed(data)
        if event_type in {'customer.subscription.updated', 'customer.subscription.deleted'}:
            await self._handle_subscription_update(data)
        return {'status': 'ok'}

    def _price_id_for_tier(self, tier: str) -> str:
        tier = normalize_tier(tier)
        if tier == 'pro':
            return self.cfg.stripe_price_pro
        if tier == 'elite':
            return self.cfg.stripe_price_elite
        return self.cfg.stripe_price_free

    def _tier_for_price_id(self, price_id: str) -> str:
        if price_id == self.cfg.stripe_price_elite:
            return 'elite'
        if price_id == self.cfg.stripe_price_pro:
            return 'pro'
        return 'free'

    def _create_checkout_session(self, user: UserContext, tier: str, price_id: str, customer_id: str | None) -> str:
        success = self.cfg.telegram_webapp_url or 'https://t.me'
        cancel = self.cfg.telegram_webapp_url or 'https://t.me'
        session = stripe.checkout.Session.create(
            mode='subscription',
            line_items=[{'price': price_id, 'quantity': 1}],
            client_reference_id=user.user_id,
            customer=customer_id,
            success_url=success,
            cancel_url=cancel,
            metadata={'user_id': user.user_id, 'tier': tier},
        )
        return session.url or ''

    def _create_billing_portal(self, customer_id: str) -> str:
        return_url = self.cfg.telegram_webapp_url or 'https://t.me'
        session = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
        return session.url

    async def _handle_checkout_completed(self, session: dict[str, Any]) -> None:
        user_id = session.get('metadata', {}).get('user_id')
        tier = session.get('metadata', {}).get('tier')
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        if not user_id or not tier:
            return
        async with get_db() as db:
            await db.execute(
                'INSERT INTO subscriptions (user_id, tier, status, provider, external_id) VALUES (?, ?, ?, ?, ?)',
                (user_id, tier, 'active', 'stripe', subscription_id),
            )
            await db.execute('UPDATE users SET tier = ?, stripe_customer_id = ? WHERE id = ?', (tier, customer_id, user_id))
            await db.commit()

    async def _handle_subscription_update(self, sub: dict[str, Any]) -> None:
        customer_id = sub.get('customer')
        status = sub.get('status')
        items = sub.get('items', {}).get('data', [])
        price_id = items[0]['price']['id'] if items else ''
        tier = self._tier_for_price_id(price_id)
        async with get_db() as db:
            user = await fetchone(db, 'SELECT id FROM users WHERE stripe_customer_id = ?', (customer_id,))
            if not user:
                return
            await db.execute(
                'INSERT INTO subscriptions (user_id, tier, status, provider, external_id) VALUES (?, ?, ?, ?, ?)',
                (user['id'], tier, status, 'stripe', sub.get('id')),
            )
            if status == 'active':
                await db.execute('UPDATE users SET tier = ? WHERE id = ?', (tier, user['id']))
            if status in {'canceled', 'unpaid', 'incomplete_expired'}:
                await db.execute('UPDATE users SET tier = ? WHERE id = ?', ('free', user['id']))
            await db.commit()
