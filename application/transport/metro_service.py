from collections import defaultdict
from typing import List
import json

from domain.metro import MetroLine, MetroStation, MetroAccess, MetroConnection, update_metro_station_with_line_info

from domain.transport_type import TransportType
from providers.api import TmbApiService
from providers.manager import LanguageManager
from providers.helpers import logger

from application.cache_service import CacheService
from .service_base import ServiceBase

class MetroService(ServiceBase):
    """
    Service to interact with Metro data via TmbApiService, with optional caching.
    """

    def __init__(self, tmb_api_service: TmbApiService, language_manager: LanguageManager, cache_service: CacheService = None):
        super().__init__(cache_service)
        self.tmb_api_service = tmb_api_service
        self.language_manager = language_manager        
        logger.info(f"[{self.__class__.__name__}] MetroService initialized")

        self.METRO_LINES_CACHE_KEY = "metro_lines"
        self.METRO_STATIONS_CACHE_KEY = "metro_stations"


    # ===== CACHE CALLS ====
    async def get_all_lines(self) -> List[MetroLine]:
        cache_key = f"metro_lines"
        cached_lines = await self._get_from_cache_or_data(cache_key, None, cache_ttl=3600*24)
        if cached_lines is not None and cached_lines:
            return cached_lines

        lines = await self.tmb_api_service.get_metro_lines()
        alerts = await self.tmb_api_service.get_global_alerts(TransportType.METRO)
        result = defaultdict(list)

        for alert in alerts:
            seen_lines = set()
            for entity in alert.get('entities', []):
                line_name = entity.get('line_name')
                if line_name and line_name not in seen_lines:
                    result[line_name].append(alert)
                    seen_lines.add(line_name)

        alerts_dict = dict(result)
        for line in lines:
            line_alerts = alerts_dict.get(line.ORIGINAL_NOM_LINIA, [])
            line.has_alerts = any(line_alerts)
            line.raw_alerts = json.dumps(line_alerts) if any(line_alerts) else ''

        return await self._get_from_cache_or_data(cache_key, lines, cache_ttl=3600*24)
    
    async def get_all_stations(self) -> List[MetroStation]:
        lines = await self.get_all_lines()
        stations = []
        for line in lines:
            stations += await self.get_stations_by_line(line.CODI_LINIA)

        return await self._get_from_cache_or_data(
            "metro_stations",
            stations,
            cache_ttl=3600*24
        )   
            
    async def get_stations_by_line(self, line_id) -> List[MetroStation]:
        cache_key = f"metro_line_{line_id}_stations"
        cached_stations = await self._get_from_cache_or_data(cache_key, None, cache_ttl=3600*24)
        if cached_stations is not None and cached_stations:
            return cached_stations
        
        line_stations = []
        line = await self.get_line_by_id(line_id)
        api_stations = await self.tmb_api_service.get_stations_by_metro_line(line_id)
        for api_station in api_stations:
            updated_station = update_metro_station_with_line_info(api_station, line)
            line_stations.append(updated_station)
        return await self._get_from_cache_or_data(cache_key, line_stations, cache_ttl=3600*24)

    async def get_station_accesses(self, group_code_id) -> List[MetroAccess]:
        return await self._get_from_cache_or_api(
            f"metro_station_{group_code_id}_accesses",
            lambda: self.tmb_api_service.get_metro_station_accesses(group_code_id),
            cache_ttl=3600*24
        )

    async def get_station_connections(self, station_id) -> List[MetroConnection]:
        connections = await self._get_from_cache_or_api(
            f"metro_station_connections_{station_id}",
            lambda: self.tmb_api_service.get_station_connections(station_id),
            cache_ttl=3600*24
        )

        formatted_connections = ("\n".join(str(c) for c in connections))
        return formatted_connections

    async def get_station_routes(self, metro_station_id):
        routes = await self._get_from_cache_or_api(
            f"metro_station_{metro_station_id}_routes",
            lambda: self.tmb_api_service.get_next_metro_at_station(metro_station_id),
            cache_ttl=10
        )
        return "\n\n".join(str(route) for route in routes)
    
    # ===== OTHER CALLS ====
    async def get_stations_by_name(self, station_name) -> List[MetroStation]:
        stations = await self.get_all_stations()
        logger.debug(f"[{self.__class__.__name__}] get_stations_by_name({station_name})")
        return self.fuzzy_search(
            query=station_name,
            items=stations,
            key=lambda stop: stop.NOM_ESTACIO
        )

    async def get_station_by_id(self, station_id) -> MetroStation:        
        stations = await self.get_all_stations()
        filtered_stations = [
            station for station in stations
            if int(station_id) == int(station.CODI_ESTACIO)
        ]

        station = filtered_stations[0] if any(filtered_stations) else None
        logger.debug(f"[{self.__class__.__name__}] get_station_by_id({station_id}) -> {station}")
        return station

    async def get_line_by_id(self, line_id) -> MetroLine:
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.CODI_LINIA) == str(line_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line}")
        return line

    async def get_line_by_name(self, line_name):
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.ORIGINAL_NOM_LINIA) == str(line_name)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_name({line_name}) -> {line}")
        return line