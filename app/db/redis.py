from redis.asyncio import ConnectionPool, Redis
from app.core.config import get_settings

_pool: ConnectionPool | None = None


def get_redis_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(get_settings().redis_url, decode_responses=True)
    return _pool


async def get_redis() -> Redis:
    return Redis(connection_pool=get_redis_pool())
