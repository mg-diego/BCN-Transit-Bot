from application.cache_service import CacheService
from .service_base import ServiceBase
from providers.api import BicingApiService
from providers.helpers import logger


class BicingService(ServiceBase):
    """
    Service to interact with Bicing data via BicingApiService, with optional caching.
    """

    def __init__(self, bicing_api_service: BicingApiService, cache_service: CacheService = None):
        super().__init__(cache_service)
        self.bicing_api_service = bicing_api_service        
        logger.info(f"[{self.__class__.__name__}] BicingService initialized")

    async def get_stations(self):
        return await self._get_from_cache_or_api(
            f"bicing_stations",
            lambda: self.bicing_api_service.get_stations(),
            cache_ttl=60
        )