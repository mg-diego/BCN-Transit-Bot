from typing import Callable, Any, List
from rapidfuzz import process, fuzz
from providers.helpers import logger
from application.cache_service import CacheService

class ServiceBase:
    """
    Base class for services that use optional caching and logging.
    """

    def __init__(self, cache_service: CacheService = None):
        self.cache_service = cache_service

    def fuzzy_search(
        self,
        query: str,
        items: List[Any],
        key: Callable[[Any], str],
        limit: int = 5,
        threshold: float = 75
    ) -> List[Any]:
        """
        Realiza una búsqueda aproximada (fuzzy) sobre una lista de objetos.

        Args:
            query: Texto a buscar.
            items: Lista de objetos.
            key: Función para extraer el campo de texto a comparar de cada objeto.
            limit: Número máximo de resultados a devolver.
            threshold: Similitud mínima (0-100) para considerar un match.

        Returns:
            Lista de objetos que coinciden con el query de manera aproximada.
        """
        item_dict = {key(item): item for item in items}

        matches = process.extract(
            query=query,
            choices=item_dict.keys(),
            scorer=fuzz.WRatio,
            limit=limit
        )

        return [item_dict[name] for name, score, _ in matches if score >= threshold] 

    async def _get_from_cache_or_api(
        self,
        cache_key: str,
        api_call: Callable[[], Any],
        cache_ttl: int = 3600
    ) -> Any:
        """
        Generic method to fetch data from cache or API with logging.
        """
        data = None
        class_name = self.__class__.__name__

        if self.cache_service:
            data = await self.cache_service.get(cache_key)
            if data:
                logger.info(f"[{class_name}] Cache hit: {cache_key}")
                return data
            else:
                logger.info(f"[{class_name}] Cache miss: {cache_key}")

        try:
            data = await api_call()
            logger.info(f"[{class_name}] Fetched data from API for key: {cache_key}")
            if self.cache_service:
                await self.cache_service.set(cache_key, data, ttl=cache_ttl)
                logger.info(f"[{class_name}] Cached data for key: {cache_key} (TTL={cache_ttl}s)")
        except Exception as e:
            logger.error(f"[{class_name}] Error fetching data for key {cache_key}: {e}")
            data = []

        return data