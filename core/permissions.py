from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.i18n import t

TIERS = ['free', 'pro', 'elite']
TIER_ORDER = {name: i for i, name in enumerate(TIERS)}

FEATURE_GATES = {
    'stocks_fundamentals': 'pro',
    'stocks_ratios': 'pro',
    'stocks_dividends': 'pro',
    'stocks_earnings': 'elite',
    'crypto_onchain': 'pro',
    'alerts_advanced': 'pro',
    'portfolio_pnl': 'pro',
    'news_project': 'pro',
    'education_quiz': 'elite',
    'admin_panel': 'elite',
}


@dataclass
class UserContext:
    platform: str
    user_id: str
    username: str | None
    tier: str
    language: str
    is_admin: bool
    badge: str = 'none'


BADGES = ['none', 'major', 'hodl', 'verified']


def has_access(user: UserContext, feature: str) -> bool:
    required = FEATURE_GATES.get(feature)
    if not required:
        return True
    return TIER_ORDER.get(user.tier, 0) >= TIER_ORDER.get(required, 0)


def missing_access_message(feature: str, lang: str = 'en') -> str:
    required = FEATURE_GATES.get(feature, 'pro')
    return t('msg.feature_requires', lang, tier=t(f'tier.{required}', lang))


def is_admin_allowed(user: UserContext) -> bool:
    return user.is_admin


def tier_badge(tier: str) -> str:
    return {
        'free': 'Free',
        'pro': 'Pro',
        'elite': 'Elite',
    }.get(tier, tier)


def normalize_tier(value: str) -> str:
    value = (value or '').lower().strip()
    if value in TIERS:
        return value
    return 'free'


def allowed_tiers() -> Iterable[str]:
    return TIERS
