from typing import List
from domain.rodalies import RodaliesLine, RodaliesStation

from providers.api import RodaliesApiService
from providers.manager import LanguageManager
from providers.helpers import logger

from application.cache_service import CacheService
from .service_base import ServiceBase

class RodaliesService(ServiceBase):
        
    def __init__(self, rodalies_api_service: RodaliesApiService, language_manager: LanguageManager, cache_service: CacheService = None):
        super().__init__(cache_service)
        self.rodalies_api_service = rodalies_api_service
        self.language_manager = language_manager        
        logger.info(f"[{self.__class__.__name__}] RodaliesService initialized")

    async def get_all_lines(self) -> List[RodaliesLine]:
        return await self._get_from_cache_or_api(
            "rodalies_lines",
            self.rodalies_api_service.get_lines,
            cache_ttl=3600*24
        )
    
    async def get_line_by_id(self, line_id: str) -> RodaliesLine:
        return await self._get_from_cache_or_api(
            f"rodalies_line_{line_id}",
            lambda: self.rodalies_api_service.get_line_by_id(line_id),
            cache_ttl=3600*24
        )
    
    async def get_stations_by_line(self, line_id) -> List[RodaliesStation]:
        """
        Retrieve stations for a specific rodalies line.
        """
        line = await self.get_line_by_id(line_id)        
        return line.stations
    
    async def get_station_by_id(self, station_id, line_id) -> RodaliesStation:
        """
        Retrieve a station by its code.
        """
        stops = await self.get_stations_by_line(line_id)
        stop = next((s for s in stops if str(s.id) == str(station_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_station_by_id({station_id}, line {line_id}) -> {stop}")
        return stop
    
    async def get_station_routes(self, station_id, line_id):
        routes = await self._get_from_cache_or_api(
            f"rodalies_station_{station_id}_routes",
            lambda: self.rodalies_api_service.get_next_trains_at_station(station_id, line_id),
            cache_ttl=10
        )
        return "\n\n".join(str(route) for route in routes)