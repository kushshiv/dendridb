import asyncio

import redis.asyncio as redis
from redis.asyncio import Redis

from dendridb.config import get_settings

WORKING_MEMORY_KEY_PREFIX = "dendridb:wm:"

_clients: dict[asyncio.AbstractEventLoop, Redis] = {}


def get_redis_client() -> Redis:
    loop = asyncio.get_running_loop()
    client = _clients.get(loop)
    if client is None:
        settings = get_settings()
        client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        _clients[loop] = client
    return client


async def check_redis_connection() -> bool:
    try:
        client = get_redis_client()
        return bool(await client.ping())
    except Exception:
        return False


async def flush_working_memory_keys() -> None:
    client = get_redis_client()
    keys: list[str] = []
    async for key in client.scan_iter(match=f"{WORKING_MEMORY_KEY_PREFIX}*"):
        keys.append(key)
    if keys:
        await client.delete(*keys)
