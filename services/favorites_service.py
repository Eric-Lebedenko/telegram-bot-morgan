from __future__ import annotations

from database import get_db, fetchall
from core.permissions import UserContext


class FavoritesService:
    async def add_favorite(self, user: UserContext, asset_type: str, symbol: str) -> bool:
        async with get_db() as db:
            cur = await db.execute(
                'INSERT OR IGNORE INTO favorites (user_id, asset_type, symbol) VALUES (?, ?, ?)',
                (user.user_id, asset_type, symbol),
            )
            await db.commit()
            return cur.rowcount > 0

    async def list_favorites(self, user: UserContext) -> list[dict[str, object]]:
        async with get_db() as db:
            rows = await fetchall(
                db,
                'SELECT asset_type, symbol, created_at FROM favorites WHERE user_id = ? ORDER BY created_at DESC',
                (user.user_id,),
            )
        return [dict(row) for row in rows]

    async def remove_favorite(self, user: UserContext, asset_type: str, symbol: str) -> int:
        async with get_db() as db:
            cur = await db.execute(
                'DELETE FROM favorites WHERE user_id = ? AND asset_type = ? AND symbol = ?',
                (user.user_id, asset_type, symbol),
            )
            await db.commit()
            return cur.rowcount
