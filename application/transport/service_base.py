from typing import Callable, Any, List
from rapidfuzz import process, fuzz
from providers.helpers import logger, HtmlHelper
from application.cache_service import CacheService
import time

class ServiceBase:
    """
    Base class for services that use optional caching and logging.
    """

    def __init__(self, cache_service: CacheService = None):
        self.cache_service = cache_service

    def log_exec_time(func):
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000
            cls = args[0].__class__.__name__ if args else "Unknown"
            logger.debug(f"[{cls}] {func.__name__} ejecutado en {elapsed:.2f} ms")
            return result
        return wrapper

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

        # --- Matches without special chars ---
        remaining_items = [item for item in items if item not in exact_matches]
        normalized_matches = [item for item in remaining_items if HtmlHelper.normalize_text(query_lower) in HtmlHelper.normalize_text(key(item).lower())]

        # --- Prepare fuzzy search excluding exact matches ---
        remaining_items = [item for item in items if item not in (exact_matches + normalized_matches)]
        item_dict = {key(item): item for item in remaining_items}

        # --- Fuzzy matches ---
        fuzzy_matches = process.extract(
            query=query,
            choices=item_dict.keys(),
            scorer=fuzz.WRatio
        )

        fuzzy_filtered = [item_dict[name] for name, score, _ in fuzzy_matches if score >= threshold]

        # --- Combine exact + normalized + fuzzy ---
        return exact_matches + normalized_matches + fuzzy_filtered

    async def _get_from_cache_or_data(
        self,
        cache_key: str,
        data: Any,
        cache_ttl: int = 3600
    ) -> Any:
        """
        Generic method to fetch data from cache or use the provided data,
        then store it in cache if needed.

        Args:
            cache_key: Key to use for caching.
            data: Pre-fetched or pre-computed data.
            cache_ttl: Time to live for the cache in seconds.

        Returns:
            The data, either from cache or the provided one.
        """
        class_name = self.__class__.__name__

        if self.cache_service:
            cached_data = await self.cache_service.get(cache_key)
            if cached_data:
                logger.debug(f"[{class_name}] Cache hit: {cache_key}")
                return cached_data
            else:
                logger.debug(f"[{class_name}] Cache miss: {cache_key}")

        # Store provided data in cache
        if self.cache_service and data is not None:
            await self.cache_service.set(cache_key, data, ttl=cache_ttl)
            logger.debug(f"[{class_name}] Cached data for key: {cache_key} (TTL={cache_ttl}s)")

        return data

    async def _get_from_cache_or_api(
        self,
        cache_key: str,
        api_call: Callable[[], Any],
        cache_ttl: int = 3600
    ) -> Any:
        """
        Fetch data from cache or, if not present, call the API function
        and store the result in cache using the base helper.

        Args:
            cache_key: Key to use for caching.
            api_call: Async callable that fetches the data.
            cache_ttl: Time to live for the cache in seconds.

        Returns:
            Data from cache or API.
        """
        class_name = self.__class__.__name__

        # Try cache first
        if self.cache_service:
            cached_data = await self.cache_service.get(cache_key)
            if cached_data:
                logger.debug(f"[{class_name}] Cache hit: {cache_key}")
                return cached_data
            else:
                logger.debug(f"[{class_name}] Cache miss: {cache_key}")

        # Fetch data from API
        try:
            data = await api_call()
            logger.debug(f"[{class_name}] Fetched data from API for key: {cache_key}")
        except Exception as e:
            logger.error(f"[{class_name}] Error fetching data for key {cache_key}: {e}")
            data = []

        # Use the generic method to cache and return
        return await self._get_from_cache_or_data(cache_key, data, cache_ttl)