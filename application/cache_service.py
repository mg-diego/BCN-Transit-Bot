import time
import asyncio
from typing import Any, Optional
from providers.helpers import logger

class CacheService:
    """In-memory cache service with optional expiration and logging."""

    def __init__(self):
        # Dictionary: key -> (value, expiration_timestamp)
        self._cache = {}
        self._lock = asyncio.Lock()
        logger.info("[CacheService] Initialized")

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Store a value in the cache.

        :param key: Cache key.
        :param value: Value to store.
        :param ttl: Optional time-to-live in seconds.
        """
        expire_at = time.time() + ttl if ttl else None
        async with self._lock:
            self._cache[key] = (value, expire_at)
        logger.info(f"[CacheService] Set key '{key}' with ttl={ttl}")

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache if not expired.
        """
        async with self._lock:
            if key in self._cache:
                value, expire_at = self._cache[key]
                if expire_at is None or expire_at > time.time():
                    logger.info(f"[CacheService] Cache hit for key '{key}'")
                    return value
                else:
                    # Expired: remove
                    del self._cache[key]
                    logger.info(f"[CacheService] Cache expired for key '{key}'")
            else:
                logger.info(f"[CacheService] Cache miss for key '{key}'")
        return None

    async def delete(self, key: str):
        """
        Delete a key from the cache.
        """
        async with self._lock:
            existed = self._cache.pop(key, None)
        if existed:
            logger.info(f"[CacheService] Deleted key '{key}' from cache")
        else:
            logger.info(f"[CacheService] Key '{key}' not found in cache for deletion")

    async def clear(self):
        """
        Clear the entire cache.
        """
        async with self._lock:
            self._cache.clear()
        logger.info("[CacheService] Cleared entire cache")
