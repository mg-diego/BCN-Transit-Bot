import time
import asyncio
from typing import Any, Optional
from providers.helpers import logger

class CacheService:
    """In-memory cache service with optional expiration and logging + timing."""

    def __init__(self):
        # Dictionary: key -> (value, expiration_timestamp)
        self._cache = {}
        self._lock = asyncio.Lock()
        logger.info("[CacheService] Initialized")

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        start = time.perf_counter()
        expire_at = time.time() + ttl if ttl else None
        async with self._lock:
            self._cache[key] = (value, expire_at)
        duration = time.perf_counter() - start
        logger.info(f"[CacheService] Set key '{key}' with ttl={ttl} in {duration:.4f}s")

    async def get(self, key: str) -> Optional[Any]:
        start = time.perf_counter()
        async with self._lock:
            if key in self._cache:
                value, expire_at = self._cache[key]
                if expire_at is None or expire_at > time.time():
                    duration = time.perf_counter() - start
                    logger.info(f"[CacheService] Cache hit for key '{key}' in {duration:.4f}s")
                    return value
                else:
                    del self._cache[key]
                    duration = time.perf_counter() - start
                    logger.info(f"[CacheService] Cache expired for key '{key}' in {duration:.4f}s")
            else:
                duration = time.perf_counter() - start
                logger.info(f"[CacheService] Cache miss for key '{key}' in {duration:.4f}s")
        return None

    async def delete(self, key: str):
        start = time.perf_counter()
        async with self._lock:
            existed = self._cache.pop(key, None)
        duration = time.perf_counter() - start
        if existed:
            logger.info(f"[CacheService] Deleted key '{key}' from cache in {duration:.4f}s")
        else:
            logger.info(f"[CacheService] Key '{key}' not found for deletion in {duration:.4f}s")

    async def clear(self):
        start = time.perf_counter()
        async with self._lock:
            self._cache.clear()
        duration = time.perf_counter() - start
        logger.info(f"[CacheService] Cleared entire cache in {duration:.4f}s")
