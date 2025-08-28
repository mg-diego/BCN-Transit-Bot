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
        static_lines = await self.cache_service.get("bus_lines_static")
        alerts_dict = await self.cache_service.get("bus_lines_alerts")

        if not static_lines:
            static_lines = await self.tmb_api_service.get_bus_lines()
            await self.cache_service.set("bus_lines_static", static_lines, ttl=3600 * 24)

        if not alerts_dict:
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
            await self.cache_service.set("bus_lines_alerts", alerts_dict, ttl=3600)

        # Combinar líneas + alertas
        for line in static_lines:
            line_alerts = alerts_dict.get(line.ORIGINAL_NOM_LINIA, [])
            line.has_alerts = bool(line_alerts)
            line.raw_alerts = json.dumps(line_alerts) if line_alerts else ""

        return static_lines
    
    async def get_all_stops(self) -> List[BusStop]:
        static_stops = await self.cache_service.get("bus_stops_static")
        alerts_by_stop = await self.cache_service.get("bus_stops_alerts")

        if not static_stops:
            static_stops = await self._build_and_cache_static_stops()

        if not alerts_by_stop:
            alerts_by_stop = await self._build_and_cache_stop_alerts()

        for stop in static_stops:
            stop_alerts = alerts_by_stop.get(stop.CODI_PARADA, [])
            stop.has_alerts = bool(stop_alerts)
            stop.alerts = json.dumps(stop_alerts) if stop_alerts else ""

        return static_stops 

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

    async def _build_and_cache_static_stops(self) -> List[BusStop]:
        stops = []
        lines = await self.get_all_lines()

        for line in lines:
            api_stops = await self.tmb_api_service.get_bus_line_stops(line.CODI_LINIA)
            for api_stop in api_stops:
                stop = update_bus_stop_with_line_info(api_stop, line)
                stops.append(stop)

        await self.cache_service.set("bus_stops_static", stops, ttl=3600 * 24)
        return stops
    
    async def _build_and_cache_stop_alerts(self) -> dict:
        alerts_by_stop = defaultdict(list)
        lines = await self.get_all_lines()

        for line in lines:
            if not line.has_alerts:
                continue

            stops = await self.get_stops_by_line(line.CODI_LINIA)
            for stop in stops:
                alerts = json.loads(line.raw_alerts)
                alerts_by_stop[stop.CODI_PARADA].extend(alerts)

        alerts_dict = dict(alerts_by_stop)
        await self.cache_service.set("bus_stops_alerts", alerts_dict, ttl=3600)
        return alerts_dict