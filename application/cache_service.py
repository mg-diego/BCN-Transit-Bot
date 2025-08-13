import time
import asyncio
from typing import Any, Optional


class CacheService:
    """Servicio de caché en memoria con expiración opcional."""

    def __init__(self):
        # Diccionario: clave -> (valor, timestamp_expiración)
        self._cache = {}
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Guarda un valor en caché.

        :param key: Clave de la caché.
        :param value: Valor a guardar.
        :param ttl: Tiempo de vida en segundos (opcional).
        """
        expire_at = time.time() + ttl if ttl else None
        async with self._lock:
            self._cache[key] = (value, expire_at)

    async def get(self, key: str) -> Optional[Any]:
        """
        Recupera un valor de la caché si no ha expirado.
        """
        async with self._lock:
            if key in self._cache:
                value, expire_at = self._cache[key]
                if expire_at is None or expire_at > time.time():
                    return value
                else:
                    # Expirado: eliminar
                    del self._cache[key]
        return None

    async def delete(self, key: str):
        """
        Elimina una clave de la caché.
        """
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self):
        """
        Limpia toda la caché.
        """
        async with self._lock:
            self._cache.clear()
