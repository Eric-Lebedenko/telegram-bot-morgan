from __future__ import annotations

import json
from database import get_db, fetchone, fetchall
from core.permissions import UserContext


class LinkService:
    async def add_link(
        self,
        user: UserContext,
        kind: str,
        provider: str,
        label: str,
        data: dict[str, object],
    ) -> int:
        async with get_db() as db:
            await db.execute(
                'INSERT INTO linked_accounts (user_id, kind, provider, label, data_json) VALUES (?, ?, ?, ?, ?)',
                (user.user_id, kind, provider, label, json.dumps(data)),
            )
            await db.commit()
            row = await fetchone(db, 'SELECT id FROM linked_accounts WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user.user_id,))
            return int(row['id']) if row else 0

    async def list_links(self, user: UserContext, kind: str | None = None) -> list[dict[str, object]]:
        async with get_db() as db:
            if kind:
                rows = await fetchall(
                    db,
                    'SELECT * FROM linked_accounts WHERE user_id = ? AND kind = ? ORDER BY created_at DESC',
                    (user.user_id, kind),
                )
            else:
                rows = await fetchall(
                    db,
                    'SELECT * FROM linked_accounts WHERE user_id = ? ORDER BY created_at DESC',
                    (user.user_id,),
                )
        result = []
        for row in rows:
            data = {}
            try:
                data = json.loads(row['data_json'] or '{}')
            except Exception:
                data = {}
            item = dict(row)
            item['data'] = data
            result.append(item)
        return result

    async def remove_link(self, user: UserContext, link_id: int) -> None:
        async with get_db() as db:
            await db.execute('DELETE FROM linked_accounts WHERE user_id = ? AND id = ?', (user.user_id, link_id))
            await db.commit()
