from typing import List
from providers.api.tmb_api_service import TmbApiService

from domain.bus import BusLine, BusStop
from providers.helpers import logger

from .service_base import ServiceBase
from application.cache_service import CacheService

class BusService(ServiceBase):
    """
    Service to interact with Bus data via TmbApiService, with optional caching.
    """

    def __init__(self, tmb_api_service: TmbApiService, cache_service: CacheService = None):
        super().__init__(cache_service)
        self.tmb_api_service = tmb_api_service        
        logger.info(f"[{self.__class__.__name__}] BusService initialized")

    async def get_all_lines(self) -> List[BusLine]:
        """
        Retrieve all bus lines. Uses cache if available.
        """
        return await self._get_from_cache_or_api(
            "bus_lines",
            self.tmb_api_service.get_bus_lines,
            cache_ttl=3600*24
        )
    
    async def get_stops_by_name(self, stop_name) -> List[BusLine]:
        stops = await self._get_from_cache_or_api(
            "bus_stops",
            self.tmb_api_service.get_bus_stops,
            cache_ttl=3600*24
        )

        filtered_stops = [
            stop
            for stop in stops
            if stop_name.lower() in stop.NOM_PARADA.lower()
        ]

        return filtered_stops

    async def get_line_by_id(self, line_id) -> BusLine:
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.CODI_LINIA) == str(line_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line}")
        return line
    
    async def get_lines_by_category(self, bus_category: str):
        lines = await self.get_all_lines()
        if "-" in bus_category:
            start, end = bus_category.split("-")
            return [
                line for line in lines
                if int(start) <= int(line.CODI_LINIA) <= int(end)
                and line.ORIGINAL_NOM_LINIA.isdigit()
            ]
        else:            
            return [
                line for line in lines
                if bus_category == line.NOM_FAMILIA
            ]

    async def get_stops_by_line(self, line_id) -> List[BusStop]:
        """
        Retrieve stops for a specific bus line.
        """
        return await self._get_from_cache_or_api(
            f"bus_line_{line_id}_stops",
            lambda: self.tmb_api_service.get_bus_line_stops(line_id),
            cache_ttl=3600*24
        )

    async def get_stop_by_id(self, stop_id) -> BusStop:
        """
        Retrieve a stop by its CODI_PARADA.
        """
        stops = await self._get_from_cache_or_api(
            "bus_stops",
            self.tmb_api_service.get_bus_stops,
            cache_ttl=3600*24
        )

        filtered_stops = [
            stop
            for stop in stops
            if int(stop_id) == int(stop.CODI_PARADA)
        ]

        return filtered_stops[0] if any(filtered_stops) else None

    async def get_stop_routes(self, stop_id: str) -> str:
        """
        Retrieve the next buses for a specific stop. Uses cache if available.
        """
        routes = await self._get_from_cache_or_api(
            f"bus_stop_{stop_id}_routes",
            lambda: self.tmb_api_service.get_next_bus_at_stop(stop_id),
            cache_ttl=10
        )
        return "\n\n".join(str(route) for route in routes)
