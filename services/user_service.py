from __future__ import annotations

from database import get_db, fetchone, fetchall
from core.permissions import normalize_tier, UserContext
from core.i18n import normalize_lang


class UserService:
    async def get_or_create_user(
        self,
        platform: str,
        platform_user_id: str,
        username: str | None,
        is_admin: bool,
        language_code: str | None = None,
    ) -> UserContext:
        language = normalize_lang(language_code)
        async with get_db() as db:
            row = await fetchone(
                db,
                'SELECT * FROM users WHERE platform = ? AND platform_user_id = ?',
                (platform, platform_user_id),
            )
            if row is None:
                await db.execute(
                    'INSERT INTO users (platform, platform_user_id, username, tier, is_admin, language) VALUES (?, ?, ?, ?, ?, ?)',
                    (platform, platform_user_id, username, 'free', 1 if is_admin else 0, language),
                )
                await db.commit()
                row = await fetchone(
                    db,
                    'SELECT * FROM users WHERE platform = ? AND platform_user_id = ?',
                    (platform, platform_user_id),
                )
            tier = normalize_tier(row['tier'])
            language = row['language'] or language
            return UserContext(
                platform=platform,
                user_id=str(row['id']),
                platform_user_id=str(platform_user_id),
                username=row['username'],
                tier=tier,
                language=language,
                is_admin=bool(row['is_admin']),
                badge=row['profile_badge'] or 'none',
            )

    async def update_tier(self, user_id: str, tier: str) -> None:
        async with get_db() as db:
            await db.execute('UPDATE users SET tier = ? WHERE id = ?', (tier, user_id))
            await db.commit()

    async def update_language(self, user_id: str, language: str) -> None:
        async with get_db() as db:
            await db.execute('UPDATE users SET language = ? WHERE id = ?', (language, user_id))
            await db.commit()

    async def get_user_stats(self) -> dict[str, str]:
        async with get_db() as db:
            total = await fetchone(db, 'SELECT COUNT(*) AS c FROM users')
            tiers = await fetchall(db, 'SELECT tier, COUNT(*) AS c FROM users GROUP BY tier')
        tier_lines = ', '.join([f"{row['tier']}: {row['c']}" for row in tiers])
        return {
            'Total Users': str(total['c']),
            'By Tier': tier_lines or 'N/A',
        }

    async def update_badge(self, user_id: str, badge: str) -> None:
        async with get_db() as db:
            await db.execute('UPDATE users SET profile_badge = ? WHERE id = ?', (badge, user_id))
            await db.commit()
