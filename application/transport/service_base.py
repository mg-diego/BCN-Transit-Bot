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
        threshold: float = 80
    ) -> List[Any]:
        """
        Performs fuzzy search on a list of objects, returning all exact matches
        plus all fuzzy matches above the threshold.

        Args:
            query: Text to search.
            items: List of objects.
            key: Function to extract the text field from each object.
            threshold: Minimum similarity (0-100) for fuzzy match.

        Returns:
            List of objects matching the query exactly or approximately.
        """
        query_lower = query.lower()

        # --- Exact matches (substring, case-insensitive) ---
        exact_matches = [item for item in items if query_lower in key(item).lower()]

        # --- Prepare fuzzy search excluding exact matches ---
        remaining_items = [item for item in items if item not in exact_matches]
        item_dict = {key(item): item for item in remaining_items}

        # --- Fuzzy matches ---
        fuzzy_matches = process.extract(
            query=query,
            choices=item_dict.keys(),
            scorer=fuzz.WRatio
        )

        fuzzy_filtered = [item_dict[name] for name, score, _ in fuzzy_matches if score >= threshold]

        # --- Combine exact + fuzzy ---
        return exact_matches + fuzzy_filtered

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