from typing import List

from providers.api import TramApiService
from providers.manager import LanguageManager
from providers.helpers import logger

from domain.tram import TramLine, TramStop, TramConnection, TramLineRoute, NextTram

from application.cache_service import CacheService
from .service_base import ServiceBase

class TramService(ServiceBase):
    """
    Service to interact with Tram data via TramApiService, with optional caching.
    """

    def __init__(self, tram_api_service: TramApiService, language_manager: LanguageManager, cache_service: CacheService = None):
        super().__init__(cache_service)        
        self.tram_api_service = tram_api_service
        self.language_manager = language_manager        
        logger.info(f"[{self.__class__.__name__}] TramService initialized")

    async def get_all_lines(self) -> List[TramLine]:
        return await self._get_from_cache_or_api(
            "tram_lines",
            self.tram_api_service.get_lines,
            cache_ttl=3600
        )

    async def get_line_by_id(self, line_id) -> TramLine:
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.code) == str(line_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line}")
        return line

    async def get_stops_by_line(self, line_id: str) -> List[TramStop]:
        return await self._get_from_cache_or_api(
            f"tram_line_{line_id}_stops",
            lambda: self.tram_api_service.get_stops_on_line(line_id),
            cache_ttl=3600
        )

    async def get_stop_by_id(self, stop_id, line_id) -> TramStop:
        stops = await self.get_stops_by_line(line_id)
        stop = next((s for s in stops if str(s.id) == str(stop_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_stop_by_id({stop_id}, line {line_id}) -> {stop}")
        return stop

    async def get_tram_stop_connections(self, stop_id) -> List[TramConnection]:
        connections = await self._get_from_cache_or_api(
            f"tram_stop_connections_{stop_id}",
            lambda: self.tram_api_service.get_connections_at_stop(stop_id),
            cache_ttl=3600
        )

        formatted_connections = (
            "\n".join(str(c) for c in connections)
            or self.language_manager.t('tram.stop.no.connections')
        )
        return formatted_connections

    async def get_stop_routes(self, outbound_code: int, return_code: int) -> str:
        routes = await self._get_from_cache_or_api(
            f"tram_routes_{outbound_code}_{return_code}",
            lambda: self.tram_api_service.get_next_trams_at_stop(outbound_code, return_code),
            cache_ttl=10
        )
        return "\n\n".join(str(route) for route in routes)
