from typing import List
from application.cache_service import CacheService
from domain.bicing.bicing_station import BicingStation
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

    async def get_all_stations(self) -> List[BicingStation]:
        return await self._get_from_cache_or_api(
            f"bicing_stations",
            lambda: self.bicing_api_service.get_stations(),
            cache_ttl=10
        )
    
    async def get_stations_by_name(self, station_name) -> List[BicingStation]:
        stations = await self.get_all_stations()
        logger.debug(f"[{self.__class__.__name__}] get_stations_by_name({station_name})")
        if station_name == '':
            return stations
        return self.fuzzy_search(
            query=station_name,
            items=stations,
            key=lambda stop: stop.streetName
        )
    
    async def get_station_by_id(self, station_id) -> BicingStation:
        stations = await self.get_all_stations()
        filtered_stations = [
            station for station in stations
            if int(station_id) == int(station.id)
        ]

        station = filtered_stations[0] if any(filtered_stations) else None
        logger.debug(f"[{self.__class__.__name__}] get_station_by_id({station_id}) -> {station}")
        return station
    
    async def get_stations_with_availability(self) -> List[BicingStation]:
        stations = await self.get_all_stations()
        return [station for station in stations if station.disponibilidad > 0]