from __future__ import annotations

import aiohttp
import asyncio


class HttpClient:
    def __init__(self, timeout: int = 10) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None
        self._lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        async with self._lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(timeout=self._timeout)
            return self._session

    async def get_json(self, url: str, params: dict | None = None, headers: dict | None = None) -> dict:
        session = await self._get_session()
        async with session.get(url, params=params, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def post_json(self, url: str, payload: dict, headers: dict | None = None) -> dict:
        session = await self._get_session()
        async with session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
