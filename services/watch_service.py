from __future__ import annotations

from database import get_db, fetchall


class WatchService:
    async def list_watch_items(self, platform: str) -> list[dict[str, object]]:
        async with get_db() as db:
            portfolio_rows = await fetchall(
                db,
                """
                SELECT u.id as user_id, u.platform_user_id, u.language, p.asset_type, p.symbol, 'portfolio' as source
                FROM users u
                JOIN portfolios pf ON pf.user_id = u.id
                JOIN portfolio_items p ON p.portfolio_id = pf.id
                WHERE u.platform = ?
                """,
                (platform,),
            )
            favorite_rows = await fetchall(
                db,
                """
                SELECT u.id as user_id, u.platform_user_id, u.language, f.asset_type, f.symbol, 'favorite' as source
                FROM users u
                JOIN favorites f ON f.user_id = u.id
                WHERE u.platform = ?
                """,
                (platform,),
            )
        items = [dict(row) for row in portfolio_rows] + [dict(row) for row in favorite_rows]
        seen: set[tuple[int, str, str]] = set()
        deduped: list[dict[str, object]] = []
        for item in items:
            key = (int(item['user_id']), str(item['asset_type']).lower(), str(item['symbol']).upper())
            if key in seen:
                continue
            seen.add(key)
            item['asset_type'] = str(item['asset_type']).lower()
            item['symbol'] = str(item['symbol']).upper()
            deduped.append(item)
        return deduped

    async def load_states(self) -> dict[tuple[int, str, str], float | None]:
        async with get_db() as db:
            rows = await fetchall(db, 'SELECT user_id, asset_type, symbol, last_price FROM price_watch')
        return {
            (int(row['user_id']), str(row['asset_type']).lower(), str(row['symbol']).upper()): row['last_price']
            for row in rows
        }

    async def upsert_state(self, user_id: int, asset_type: str, symbol: str, price: float | None, notified: bool) -> None:
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO price_watch (user_id, asset_type, symbol, last_price, last_notified_at, updated_at)
                VALUES (?, ?, ?, ?, CASE WHEN ? THEN datetime('now') ELSE NULL END, datetime('now'))
                ON CONFLICT(user_id, asset_type, symbol) DO UPDATE SET
                    last_price = excluded.last_price,
                    last_notified_at = CASE WHEN ? THEN datetime('now') ELSE price_watch.last_notified_at END,
                    updated_at = datetime('now')
                """,
                (user_id, asset_type, symbol, price, 1 if notified else 0, 1 if notified else 0),
            )
            await db.commit()
