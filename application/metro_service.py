from typing import List
from domain.metro.metro_line import MetroLine
from domain.metro.metro_station import MetroStation
from domain.metro.metro_access import MetroAccess
from domain.metro.metro_connection import MetroConnection
from providers.transport_api_service import TransportApiService
from providers.language_manager import LanguageManager
from application.cache_service import CacheService
from providers import logger

from .service_base import ServiceBase

class MetroService(ServiceBase):
    """
    Service to interact with Metro data via TransportApiService, with optional caching.
    """

    def __init__(self, transport_api_service: TransportApiService, language_manager: LanguageManager, cache_service: CacheService = None):
        super().__init__(cache_service)
        self.transport_api_service = transport_api_service
        self.language_manager = language_manager        
        logger.info(f"[{self.__class__.__name__}] MetroService initialized")

    async def get_all_lines(self) -> List[MetroLine]:
        return await self._get_from_cache_or_api(
            "metro_lines",
            self.transport_api_service.get_metro_lines,
            cache_ttl=3600
        )

    async def get_line_by_id(self, line_id) -> MetroLine:
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.CODI_LINIA) == str(line_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line}")
        return line

    async def get_stations_by_line(self, line_id) -> List[MetroStation]:
        return await self._get_from_cache_or_api(
            f"metro_line_{line_id}_stations",
            lambda: self.transport_api_service.get_stations_by_metro_line(line_id),
            cache_ttl=3600
        )

    async def get_station_accesses(self, group_code_id) -> List[MetroAccess]:
        return await self._get_from_cache_or_api(
            f"metro_station_{group_code_id}_accesses",
            lambda: self.transport_api_service.get_metro_station_accesses(group_code_id),
            cache_ttl=3600
        )

    async def get_station_by_id(self, station_id, line_id) -> MetroStation:
        stations = await self.get_stations_by_line(line_id)
        station = next((s for s in stations if str(s.CODI_ESTACIO) == str(station_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_station_by_id({station_id}, line {line_id}) -> {station}")
        return station

    async def get_metro_station_connections(self, station_id) -> List[MetroConnection]:
        connections = await self._get_from_cache_or_api(
            f"metro_station_connections_{station_id}",
            lambda: self.transport_api_service.get_metro_station_connections(station_id),
            cache_ttl=3600
        )

        formatted_connections = (
            "\n".join(str(c) for c in connections)
            or self.language_manager.t('metro.station.no.connections')
        )
        return formatted_connections

    async def get_metro_station_alerts(self, metro_line_id, station_id):
        line = await self.get_line_by_id(metro_line_id)
        alerts = await self._get_from_cache_or_api(
            f"metro_station_alerts_{station_id}",
            lambda: self.transport_api_service.get_metro_station_alerts(line.ORIGINAL_NOM_LINIA, station_id),
            cache_ttl=3600
        )

        formatted_alerts = (
            "\n".join(f"<pre>{c}</pre>" for c in alerts)
            or self.language_manager.t('metro.station.no.alerts')
        )
        return formatted_alerts

    async def get_station_routes(self, metro_station_id):
        routes = await self._get_from_cache_or_api(
            f"metro_station_{metro_station_id}_routes",
            lambda: self.transport_api_service.get_next_metro_at_station(metro_station_id),
            cache_ttl=10
        )
        return "\n\n".join(str(route) for route in routes)
