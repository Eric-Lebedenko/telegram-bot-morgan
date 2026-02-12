from __future__ import annotations

from database import get_db, fetchall
from core.permissions import UserContext


class AlertService:
    async def add_alert(self, user: UserContext, asset_type: str, symbol: str, condition: str, target: float) -> None:
        async with get_db() as db:
            await db.execute(
                'INSERT INTO alerts (user_id, asset_type, symbol, condition, target_value) VALUES (?, ?, ?, ?, ?)',
                (user.user_id, asset_type, symbol, condition, target),
            )
            await db.commit()

    async def list_alerts(self, user: UserContext) -> list[dict[str, str]]:
        async with get_db() as db:
            rows = await fetchall(db, 'SELECT * FROM alerts WHERE user_id = ? AND is_active = 1', (user.user_id,))
        return [dict(row) for row in rows]
