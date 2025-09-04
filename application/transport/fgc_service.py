from typing import List
import json

from domain.fgc import FgcLine, FgcStation
from providers.api import FgcApiService
from providers.manager import LanguageManager
from providers.helpers import logger

from application.cache_service import CacheService
from providers.manager.user_data_manager import UserDataManager
from domain.transport_type import TransportType
from .service_base import ServiceBase

class FgcService(ServiceBase):
    """
    Service to interact with Metro data via TmbApiService, with optional caching.
    """

    def __init__(self, fgc_api_service: FgcApiService, language_manager: LanguageManager, cache_service: CacheService = None, user_data_manager: UserDataManager = None):
        super().__init__(cache_service)
        self.fgc_api_service = fgc_api_service
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager
        logger.info(f"[{self.__class__.__name__}] FgcService initialized")

    # ===== CACHE CALLS ====
    async def get_all_lines(self) -> List[FgcLine]:
        return await self._get_from_cache_or_api(
            "fgc_lines",
            lambda: self.fgc_api_service.get_all_lines(),
            cache_ttl=3600*24
        )
    
    async def get_all_stations(self) -> List[FgcStation]:
        #TODO: Complete integration
        fgc_stations_key = "fgc_stations"
        #moute_stations_key = "moute_stations"

        cached_stations = await self._get_from_cache_or_data(fgc_stations_key, None, cache_ttl=3600*24)
        #moute_stations = await self._get_from_cache_or_data(moute_stations_key, None, cache_ttl=3600*24)

        if cached_stations is not None:
            return cached_stations
        
        #if moute_stations is None:
        #    moute_stations = await self.fgc_api_service.get_all_stations()
        #    await self._get_from_cache_or_data(moute_stations_key, moute_stations, cache_ttl=3600*24)

        lines = await self.get_all_lines()
        stations = []
        for line in lines:
            line_stations = await self.fgc_api_service.get_stations_by_line(line.id)
            '''
            for line_station in line_stations:
                moute_station = next((s for s in moute_stations if str(TransportType.FGC.id) in s.get('tipusTransports') and line_station.name in s.get('desc')), None)
                if moute_station is None:
                    pass
                line_station.moute_id = moute_station.get('id')
            '''
            stations += line_stations

        return await self._get_from_cache_or_data(fgc_stations_key, stations, cache_ttl=3600*24)

    
    async def get_stations_by_line(self, line_id) -> List[FgcStation]:
        stations = await self.get_all_stations()
        return [s for s in stations if s.line_id == line_id]
    
    async def get_station_routes(self):
        salidas = await self.fgc_api_service.get_realtime_departures("Muntaner", "L6", limit=5)
        print(salidas)
