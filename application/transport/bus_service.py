from collections import defaultdict
import json
from typing import List

from domain.bus.bus_stop import update_bus_stop_with_line_info
from domain.transport_type import TransportType
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

    # === CACHE CALLS ===
    async def get_all_lines(self) -> List[BusLine]:
        cache_key = f"bus_lines"
        cached_lines = await self._get_from_cache_or_data(cache_key, None, cache_ttl=3600*24)
        if cached_lines is not None and cached_lines:
            return cached_lines

        lines = await self.tmb_api_service.get_bus_lines()
        alerts = await self.tmb_api_service.get_global_alerts(TransportType.BUS)
        result = defaultdict(list)

        for alert in alerts:
            seen_lines = set()

            for line in alert.get("linesAffected", []):
                line_id = line.get("commercialLineId")
                if line_id and line_id not in seen_lines:
                    result[line_id].append(alert)
                    seen_lines.add(line_id)

        alerts_dict = dict(result)
        for line in lines:
            line_alerts = alerts_dict.get(line.ORIGINAL_NOM_LINIA, [])
            line.has_alerts = any(line_alerts)
            line.raw_alerts = json.dumps(line_alerts) if any(line_alerts) else ''

        return await self._get_from_cache_or_data(cache_key, lines, cache_ttl=3600*24)
    
    async def get_all_stops(self) -> List[BusLine]:
        lines = await self.get_all_lines()
        stops = []
        for line in lines:
            line_stops = await self.get_stops_by_line(line.CODI_LINIA)
            stops += line_stops

        return await self._get_from_cache_or_data(
            "bus_stops",
            stops,
            cache_ttl=3600*24
        )    

    async def get_stops_by_line(self, line_id) -> List[BusStop]:
        cache_key = f"bus_line_{line_id}_stops"
        cached_stations = await self._get_from_cache_or_data(cache_key, None, cache_ttl=3600*24)
        if cached_stations is not None and cached_stations:
            return cached_stations
        
        line_stops = []
        line = await self.get_line_by_id(line_id)
        api_stops = await self.tmb_api_service.get_bus_line_stops(line_id)
        for api_stop in api_stops:
            updated_stop = update_bus_stop_with_line_info(api_stop, line)
            line_stops.append(updated_stop)
        return await self._get_from_cache_or_data(cache_key, line_stops, cache_ttl=3600*24)
    
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
    
    # === OTHER CALLS ===
    async def get_stops_by_name(self, stop_name) -> List[BusLine]:
        stops = await self.get_all_stops()
        return self.fuzzy_search(
            query=stop_name,
            items=stops,
            key=lambda stop: stop.NOM_PARADA
        )

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

    async def get_stop_by_id(self, stop_id) -> BusStop:
        """
        Retrieve a stop by its CODI_PARADA.
        """
        stops = await self.get_all_stops()
        filtered_stops = [
            stop for stop in stops
            if int(stop_id) == int(stop.CODI_PARADA)
        ]

        return next((bs for bs in filtered_stops if bs.has_alerts), filtered_stops[0] if filtered_stops else None)