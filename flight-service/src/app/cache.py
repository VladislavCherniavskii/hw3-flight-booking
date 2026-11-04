import json
import logging
from redis.asyncio.sentinel import Sentinel
from src.app.config import REDIS_SENTINELS, REDIS_MASTER_NAME

logger = logging.getLogger("cache")

sentinel = Sentinel(REDIS_SENTINELS, socket_timeout=1.0)
master = sentinel.master_for(REDIS_MASTER_NAME, socket_timeout=1.0)


async def get(key: str) -> dict | None:
    try:
        raw = await master.get(key)
        if raw is None:
            logger.info(f"CACHE MISS: {key}")
            return None
        logger.info(f"CACHE HIT: {key}")
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Redis GET error: {e}")
        return None


async def set(key: str, value: dict, ttl: int = 300) -> None:
    try:
        await master.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.warning(f"Redis SET error: {e}")


async def delete(*keys: str) -> None:
    try:
        if keys:
            await master.delete(*keys)
    except Exception as e:
        logger.warning(f"Redis DEL error: {e}")


async def delete_pattern(pattern: str) -> None:
    try:
        keys = []
        async for key in master.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await master.delete(*keys)
    except Exception as e:
        logger.warning(f"Redis pattern DEL error: {e}")
