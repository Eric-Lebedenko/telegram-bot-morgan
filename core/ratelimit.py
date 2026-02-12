from __future__ import annotations

import time
import asyncio
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests: int = 12, window_seconds: int = 10) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        now = time.time()
        async with self._lock:
            dq = self._events[key]
            while dq and now - dq[0] > self.window_seconds:
                dq.popleft()
            if len(dq) >= self.max_requests:
                return False
            dq.append(now)
            return True
