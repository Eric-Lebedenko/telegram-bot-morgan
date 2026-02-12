from __future__ import annotations

from database import get_db, fetchone, fetchall
import csv
import io
from core.permissions import UserContext


class PortfolioService:
    async def add_asset(
        self,
        user: UserContext,
        asset_type: str,
        symbol: str,
        amount: float,
        cost_basis: float,
        source: str = 'manual',
        external_id: str | None = None,
    ) -> None:
        async with get_db() as db:
            row = await fetchone(db, 'SELECT id FROM portfolios WHERE user_id = ?', (user.user_id,))
            if row is None:
                await db.execute('INSERT INTO portfolios (user_id, name) VALUES (?, ?)', (user.user_id, 'Main'))
                await db.commit()
                row = await fetchone(db, 'SELECT id FROM portfolios WHERE user_id = ?', (user.user_id,))
            portfolio_id = row['id']
            await db.execute(
                'INSERT INTO portfolio_items (portfolio_id, asset_type, symbol, amount, cost_basis, source, external_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (portfolio_id, asset_type, symbol, amount, cost_basis, source, external_id),
            )
            await db.commit()

    async def remove_asset(self, user: UserContext, symbol: str) -> int:
        async with get_db() as db:
            row = await fetchone(db, 'SELECT id FROM portfolios WHERE user_id = ?', (user.user_id,))
            if row is None:
                return 0
            portfolio_id = row['id']
            cur = await db.execute('DELETE FROM portfolio_items WHERE portfolio_id = ? AND symbol = ?', (portfolio_id, symbol))
            await db.commit()
            return cur.rowcount

    async def get_allocation(self, user: UserContext) -> dict[str, str]:
        async with get_db() as db:
            row = await fetchone(db, 'SELECT id FROM portfolios WHERE user_id = ?', (user.user_id,))
            if row is None:
                return {'Status': 'No holdings yet.'}
            portfolio_id = row['id']
            items = await fetchall(
                db,
                'SELECT asset_type, COUNT(*) as c FROM portfolio_items WHERE portfolio_id = ? GROUP BY asset_type',
                (portfolio_id,),
            )
        return {row['asset_type']: str(row['c']) for row in items} or {'Status': 'No holdings yet.'}

    async def get_pnl(self, user: UserContext) -> dict[str, str]:
        return {'Unrealized PnL': 'N/A', 'Realized PnL': 'N/A'}

    async def list_assets(self, user: UserContext) -> list[dict[str, object]]:
        async with get_db() as db:
            row = await fetchone(db, 'SELECT id FROM portfolios WHERE user_id = ?', (user.user_id,))
            if row is None:
                return []
            portfolio_id = row['id']
            items = await fetchall(
                db,
                'SELECT asset_type, symbol, amount, cost_basis, created_at FROM portfolio_items WHERE portfolio_id = ? ORDER BY created_at DESC',
                (portfolio_id,),
            )
        return [dict(item) for item in items]

    async def replace_assets(self, user: UserContext, items: list[dict[str, object]], source: str) -> int:
        async with get_db() as db:
            row = await fetchone(db, 'SELECT id FROM portfolios WHERE user_id = ?', (user.user_id,))
            if row is None:
                await db.execute('INSERT INTO portfolios (user_id, name) VALUES (?, ?)', (user.user_id, 'Main'))
                await db.commit()
                row = await fetchone(db, 'SELECT id FROM portfolios WHERE user_id = ?', (user.user_id,))
            portfolio_id = row['id']
            await db.execute('DELETE FROM portfolio_items WHERE portfolio_id = ? AND source = ?', (portfolio_id, source))
            for item in items:
                await db.execute(
                    'INSERT INTO portfolio_items (portfolio_id, asset_type, symbol, amount, cost_basis, source, external_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (
                        portfolio_id,
                        item.get('asset_type', 'crypto'),
                        item.get('symbol'),
                        float(item.get('amount') or 0),
                        float(item.get('cost_basis') or 0),
                        source,
                        item.get('external_id'),
                    ),
                )
            await db.commit()
        return len(items)

    async def export_csv(self, user: UserContext) -> str:
        items = await self.list_assets(user)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['asset_type', 'symbol', 'amount', 'cost_basis', 'source'])
        for item in items:
            writer.writerow([
                item.get('asset_type', ''),
                item.get('symbol', ''),
                item.get('amount', ''),
                item.get('cost_basis', ''),
                item.get('source', ''),
            ])
        return output.getvalue()

    async def import_csv(self, user: UserContext, csv_text: str, replace: bool = True, source: str = 'csv') -> int:
        if not csv_text.strip():
            return 0
        if replace:
            await self.replace_assets(user, [], source)

        reader = csv.DictReader(io.StringIO(csv_text))
        count = 0
        for row in reader:
            asset_type = _pick(row, ['asset_type', 'type', 'asset', 'category'], default='crypto')
            symbol = _pick(row, ['symbol', 'ticker', 'asset', 'coin', 'currency'])
            amount = _pick(row, ['amount', 'qty', 'quantity', 'balance'])
            cost_basis = _pick(row, ['cost_basis', 'cost', 'price', 'avg_price', 'purchase_price'], default='0')
            if not symbol or amount is None:
                continue
            try:
                amount_f = float(str(amount).replace(',', '').strip())
                cost_f = float(str(cost_basis).replace(',', '').strip())
            except Exception:
                continue
            await self.add_asset(user, str(asset_type).lower(), str(symbol).upper(), amount_f, cost_f, source=source)
            count += 1
        return count


def _pick(row: dict[str, object], keys: list[str], default: str | None = None) -> str | None:
    for key in keys:
        for k, v in row.items():
            if k and k.strip().lower() == key:
                return str(v).strip()
    return default
