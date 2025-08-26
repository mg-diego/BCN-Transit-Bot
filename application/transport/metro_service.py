from typing import List

from domain.metro import MetroLine, MetroStation, MetroAccess, MetroConnection

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

    async def get_all_lines(self) -> List[MetroLine]:
        return await self._get_from_cache_or_api(
            "metro_lines",
            self.tmb_api_service.get_metro_lines,
            cache_ttl=3600*24
        )

    async def get_stations_by_name(self, station_name) -> List[MetroStation]:
        stations = await self._get_from_cache_or_api(
            "metro_stations",
            self.tmb_api_service.get_metro_stations,
            cache_ttl=3600*24
        )
        return self.fuzzy_search(
            query=station_name,
            items=stations,
            key=lambda stop: stop.NOM_ESTACIO
        )

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
        
    async def get_stations_by_line(self, line_id) -> List[MetroStation]:
        return await self._get_from_cache_or_api(
            f"metro_line_{line_id}_stations",
            lambda: self.tmb_api_service.get_stations_by_metro_line(line_id),
            cache_ttl=3600*24
        )

    async def get_station_accesses(self, group_code_id) -> List[MetroAccess]:
        return await self._get_from_cache_or_api(
            f"metro_station_{group_code_id}_accesses",
            lambda: self.tmb_api_service.get_metro_station_accesses(group_code_id),
            cache_ttl=3600*24
        )

    async def get_station_by_id(self, station_id) -> MetroStation:        
        stations = await self._get_from_cache_or_api(
            "metro_stations",
            self.tmb_api_service.get_metro_stations,
            cache_ttl=3600*24
        )

        filtered_stations = [
            station for station in stations
            if int(station_id) == int(station.ID_ESTACIO)
        ]

        station = filtered_stations[0] if any(filtered_stations) else None
        logger.debug(f"[{self.__class__.__name__}] get_station_by_id({station_id}) -> {station}")
        return station

    async def get_metro_station_connections(self, station_id) -> List[MetroConnection]:
        connections = await self._get_from_cache_or_api(
            f"metro_station_connections_{station_id}",
            lambda: self.tmb_api_service.get_metro_station_connections(station_id),
            cache_ttl=3600*24
        )

        formatted_connections = (
            "\n".join(str(c) for c in connections)
            or self.language_manager.t('common.no.connections', type="metro")
        )
        return formatted_connections

    async def get_metro_station_alerts(self, metro_line_id, station_id, language):
        line = await self.get_line_by_id(metro_line_id)
        alerts = await self._get_from_cache_or_api(
            f"metro_station_alerts_{station_id}",
            lambda: self.tmb_api_service.get_metro_station_alerts(line.ORIGINAL_NOM_LINIA, station_id, language),
            cache_ttl=3600
        )

        formatted_alerts = (
            "\n".join(f"<pre>{c}</pre>" for c in alerts)
        )
        return formatted_alerts

    async def get_station_routes(self, metro_station_id):
        routes = await self._get_from_cache_or_api(
            f"metro_station_{metro_station_id}_routes",
            lambda: self.tmb_api_service.get_next_metro_at_station(metro_station_id),
            cache_ttl=10
        )
        return "\n\n".join(str(route) for route in routes)