from __future__ import annotations

import os
import aiosqlite
from typing import AsyncIterator
from contextlib import asynccontextmanager
from config import load_config

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    platform_user_id TEXT NOT NULL,
    username TEXT,
    tier TEXT NOT NULL DEFAULT 'free',
    is_admin INTEGER NOT NULL DEFAULT 0,
    stripe_customer_id TEXT,
    language TEXT NOT NULL DEFAULT 'ru',
    profile_badge TEXT DEFAULT 'none',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(platform, platform_user_id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tier TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    ends_at TEXT,
    provider TEXT,
    external_id TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS portfolio_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    asset_type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    amount REAL NOT NULL,
    cost_basis REAL NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    external_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(portfolio_id) REFERENCES portfolios(id)
);

CREATE TABLE IF NOT EXISTS linked_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    provider TEXT NOT NULL,
    label TEXT NOT NULL,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset_type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    condition TEXT NOT NULL,
    target_value REAL NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset_type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, asset_type, symbol),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS price_watch (
    user_id INTEGER NOT NULL,
    asset_type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    last_price REAL,
    last_notified_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY(user_id, asset_type, symbol),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    status TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL,
    external_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    display_name TEXT,
    headline TEXT,
    bio TEXT,
    location TEXT,
    website TEXT,
    email TEXT,
    phone TEXT,
    telegram TEXT,
    instagram TEXT,
    twitter TEXT,
    linkedin TEXT,
    company TEXT,
    role TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS feature_toggles (
    key TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    metadata TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _sqlite_path_from_url(url: str) -> str:
    if url.startswith('sqlite+aiosqlite:///'):
        return url.replace('sqlite+aiosqlite:///', '')
    if url.startswith('sqlite:///'):
        return url.replace('sqlite:///', '')
    return url


def _ensure_db_dir(db_path: str) -> None:
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    cfg = load_config()
    db_path = _sqlite_path_from_url(cfg.database_url)
    _ensure_db_dir(db_path)
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    try:
        await conn.execute('PRAGMA foreign_keys=ON;')
        yield conn
    finally:
        await conn.close()


async def init_db() -> None:
    cfg = load_config()
    db_path = _sqlite_path_from_url(cfg.database_url)
    _ensure_db_dir(db_path)
    async with aiosqlite.connect(db_path) as conn:
        await conn.executescript(SCHEMA_SQL)
        await _ensure_column(conn, 'users', 'stripe_customer_id', 'ALTER TABLE users ADD COLUMN stripe_customer_id TEXT')
        await _ensure_column(conn, 'users', 'language', "ALTER TABLE users ADD COLUMN language TEXT NOT NULL DEFAULT 'ru'")
        await _ensure_column(conn, 'users', 'profile_badge', "ALTER TABLE users ADD COLUMN profile_badge TEXT DEFAULT 'none'")
        await _ensure_column(conn, 'portfolio_items', 'source', "ALTER TABLE portfolio_items ADD COLUMN source TEXT NOT NULL DEFAULT 'manual'")
        await _ensure_column(conn, 'portfolio_items', 'external_id', 'ALTER TABLE portfolio_items ADD COLUMN external_id TEXT')
        await conn.commit()


async def fetchone(db: aiosqlite.Connection, query: str, params: tuple = ()) -> aiosqlite.Row | None:
    cur = await db.execute(query, params)
    row = await cur.fetchone()
    await cur.close()
    return row


async def fetchall(db: aiosqlite.Connection, query: str, params: tuple = ()) -> list[aiosqlite.Row]:
    cur = await db.execute(query, params)
    rows = await cur.fetchall()
    await cur.close()
    return rows


async def _ensure_column(conn: aiosqlite.Connection, table: str, column: str, ddl: str) -> None:
    cur = await conn.execute(f'PRAGMA table_info({table})')
    rows = await cur.fetchall()
    await cur.close()
    existing = {row[1] for row in rows}
    if column not in existing:
        await conn.execute(ddl)
