from __future__ import annotations

import json
from typing import Any

from app.db.redis import get_redis
from app.core.config import get_settings


class CacheService:
    def __init__(self, prefix: str = "mcp") -> None:
        self._prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    async def get(self, key: str) -> Any | None:
        redis = await get_redis()
        raw = await redis.get(self._key(key))
        return json.loads(raw) if raw else None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        redis = await get_redis()
        ttl = ttl or get_settings().cache_ttl_seconds
        await redis.setex(self._key(key), ttl, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        redis = await get_redis()
        await redis.delete(self._key(key))

    async def get_or_set(self, key: str, factory, ttl: int | None = None) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        await self.set(key, value, ttl)
        return value


cache = CacheService()
