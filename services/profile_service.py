from __future__ import annotations

from database import get_db, fetchone
from core.permissions import UserContext


PROFILE_FIELDS = [
    'display_name',
    'headline',
    'bio',
    'location',
    'website',
    'email',
    'phone',
    'telegram',
    'instagram',
    'twitter',
    'linkedin',
    'company',
    'role',
]


class ProfileService:
    async def get_profile(self, user: UserContext) -> dict[str, object]:
        async with get_db() as db:
            row = await fetchone(db, 'SELECT * FROM user_profiles WHERE user_id = ?', (user.user_id,))
        return dict(row) if row else {}

    async def get_profile_by_platform(self, platform: str, platform_user_id: str) -> dict[str, object] | None:
        async with get_db() as db:
            row = await fetchone(
                db,
                """
                SELECT p.*, u.username
                FROM users u
                JOIN user_profiles p ON p.user_id = u.id
                WHERE u.platform = ? AND u.platform_user_id = ?
                """,
                (platform, platform_user_id),
            )
        return dict(row) if row else None

    async def set_field(self, user: UserContext, field: str, value: str | None) -> None:
        field = field.strip()
        if field not in PROFILE_FIELDS:
            return
        async with get_db() as db:
            row = await fetchone(db, 'SELECT id FROM user_profiles WHERE user_id = ?', (user.user_id,))
            if row is None:
                await db.execute('INSERT INTO user_profiles (user_id) VALUES (?)', (user.user_id,))
            await db.execute(
                f'UPDATE user_profiles SET {field} = ?, updated_at = datetime(\'now\') WHERE user_id = ?',
                (value, user.user_id),
            )
            await db.commit()
