from typing import List, Callable, Any
from providers.transport_api_service import TransportApiService
from application.cache_service import CacheService
from domain.bus.bus_line import BusLine
from domain.bus.bus_stop import BusStop
from providers import logger
from .service_base import ServiceBase

class BusService(ServiceBase):
    """
    Service to interact with Bus data via TransportApiService, with optional caching.
    """

    def __init__(self, transport_api_service: TransportApiService, cache_service: CacheService = None):
        super().__init__(cache_service)
        self.transport_api_service = transport_api_service        
        logger.info(f"[{self.__class__.__name__}] BusService initialized")

    async def get_all_lines(self) -> List[BusLine]:
        """
        Retrieve all bus lines. Uses cache if available.
        """
        return await self._get_from_cache_or_api(
            "bus_lines",
            self.transport_api_service.get_bus_lines,
            cache_ttl=3600
        )

    async def get_line_by_id(self, line_id) -> BusLine:
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.CODI_LINIA) == str(line_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line}")
        return line

    async def get_stops_by_line(self, line_id) -> List[BusStop]:
        """
        Retrieve stops for a specific bus line.
        """
        return await self._get_from_cache_or_api(
            f"bus_line_{line_id}_stops",
            lambda: self.transport_api_service.get_bus_line_stops(line_id),
            cache_ttl=3600
        )

    async def get_stop_by_id(self, stop_id, line_id) -> BusStop:
        """
        Retrieve a stop by its CODI_PARADA.
        """
        stops = await self.get_stops_by_line(line_id)
        stop = next((s for s in stops if str(s.CODI_PARADA) == str(stop_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_stop_by_id({stop_id}, line {line_id}) -> {stop}")
        return stop

    async def get_stop_routes(self, stop_id: str) -> str:
        """
        Retrieve the next buses for a specific stop. Uses cache if available.
        """
        routes = await self._get_from_cache_or_api(
            f"bus_stop_{stop_id}_routes",
            lambda: self.transport_api_service.get_next_bus_at_stop(stop_id),
            cache_ttl=10
        )
        return "\n\n".join(str(route) for route in routes)
