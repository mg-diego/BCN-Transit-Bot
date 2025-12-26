import asyncio
import time
from collections import defaultdict
from typing import List

from domain.common.alert import Alert
from domain.common.connections import Connections
from domain.common.line_route import LineRoute
from domain.common.line_route import LineRoute
from domain.transport_type import TransportType
from providers.api import TramApiService
from providers.manager import LanguageManager, UserDataManager
from providers.helpers import logger

from domain.tram import TramLine, TramStation, TramConnection
from application.services.cache_service import CacheService
from .service_base import ServiceBase


class TramService(ServiceBase):
    """
    Service to interact with Tram data via TramApiService, with optional caching.
    """

    def __init__(
        self,
        tram_api_service: TramApiService,
        language_manager: LanguageManager,
        cache_service: CacheService = None,
        user_data_manager: UserDataManager = None
    ):
        start = time.perf_counter()
        super().__init__(cache_service)
        self.tram_api_service = tram_api_service
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] TramService initialized (tiempo: {elapsed:.4f} s)")

    # === CACHE CALLS ===
    async def get_all_lines(self) -> List[TramLine]:
        start = time.perf_counter()

        static_key = "tram_lines_static"
        alerts_key = "tram_lines_alerts"

        cached_lines = await self._get_from_cache_or_data(static_key, None, cache_ttl=3600*24)
        cached_alerts = await self._get_from_cache_or_data(alerts_key, None, cache_ttl=3600)

        if cached_lines:
            if cached_alerts:
                for line in cached_lines:
                    line_alerts = cached_alerts.get(line.name, [])
                    line.has_alerts = bool(line_alerts)
                    line.alerts = line_alerts
            elapsed = (time.perf_counter() - start)
            logger.info(f"[{self.__class__.__name__}] get_all_lines() from cache -> {len(cached_lines)} lines (tiempo: {elapsed:.4f} s)")
            return cached_lines

        # No hay caché, pedimos a la API
        lines, api_alerts = await asyncio.gather(
            self.tram_api_service.get_lines(),
            self.tram_api_service.get_global_alerts()
        )

        alerts = [Alert.map_from_tram_alert(a) for a in api_alerts]
        result = defaultdict(list)

        for alert in alerts:
            await self.user_data_manager.register_alert(TransportType.TRAM, alert)
            seen_lines = set()
            for entity in alert.affected_entities:
                if entity.line_name and entity.line_name not in seen_lines:
                    result[entity.line_name].append(alert)
                    seen_lines.add(entity.line_name)

        alerts_dict = dict(result)

        for line in lines:
            line_stops = await self.get_stops_by_line(line.id)
            line.description = f"{line_stops[0].name} - {line_stops[-1].name}"
            line_alerts = alerts_dict.get(line.name, [])
            line.has_alerts = bool(line_alerts)
            line.alerts = line_alerts

        await asyncio.gather(
            self._get_from_cache_or_data(static_key, lines, cache_ttl=3600*24),
            self._get_from_cache_or_data(alerts_key, alerts_dict, cache_ttl=3600)
        )

        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_all_lines() -> {len(lines)} lines (tiempo: {elapsed:.4f} s)")
        return lines

    async def get_all_stops(self) -> List[TramStation]:
        start = time.perf_counter()

        cached_stops = await self.cache_service.get("tram_stops")
        if cached_stops:
            elapsed = (time.perf_counter() - start)
            logger.info(f"[{self.__class__.__name__}] get_all_stops() from cache -> {len(cached_stops)} stops (tiempo: {elapsed:.4f} s)")
            return cached_stops

        lines = await self.get_all_lines()

        stops_lists = await asyncio.gather(
            *[self.get_stops_by_line(line.id) for line in lines]
        )

        all_stops: List[TramStation] = []
        for line, line_stops in zip(lines, stops_lists):
            all_stops.extend(TramStation.update_line_info(s, line) for s in line_stops)
        await self.cache_service.set("tram_stops", all_stops, ttl=3600*24)

        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_all_stops() -> {len(all_stops)} stops (tiempo: {elapsed:.4f} s)")
        return all_stops

    async def get_stops_by_line(self, line_id: str) -> List[TramStation]:
        start = time.perf_counter()
        stops = await self._get_from_cache_or_api(
            f"tram_line_{line_id}_stops",
            lambda: self.tram_api_service.get_stops_on_line(line_id),
            cache_ttl=3600*24
        )
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_stops_by_line({line_id}) -> {len(stops)} stops (tiempo: {elapsed:.4f} s)")
        return stops

    async def get_stop_routes(self, stop_code: int) -> List[LineRoute]:
        start = time.perf_counter()
        stop = await self.get_stop_by_code(stop_code)
        routes = await self._get_from_cache_or_api(
            f"tram_routes_{stop_code}",
            lambda: self.tram_api_service.get_next_trams_at_stop(stop.outboundCode, stop.returnCode),
            cache_ttl=30,
        )
        lines = await self.get_all_lines()
        for route in routes:
            if line := next((l for l in lines if l.name == route.line_name), None):
                route.line_id = line.id
                route.line_code = line.code
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_stop_routes({stop_code}) -> {len(routes)} routes (tiempo: {elapsed:.4f} s)")
        return routes

    async def get_tram_stop_connections(self, stop_code) -> Connections:
        start = time.perf_counter()
        connections = await self.cache_service.get(f"tram_stop_connections_{stop_code}")
        if connections:
            elapsed = (time.perf_counter() - start)
            logger.info(f"[{self.__class__.__name__}] get_tram_stop_connections({stop_code}) from cache -> {len(connections)} connections (tiempo: {elapsed:.4f} s)")
            return connections
        
        same_stops = [s for s in await self.get_all_stops() if s.code == stop_code]
        connections = [TramLine.create_tram_connection(s.line_id, s.line_code, s.line_name, s.line_description, '', '') for s in same_stops]
        await self.cache_service.set(f"tram_stop_connections_{stop_code}", connections, ttl=3600*24)

        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_tram_stop_connections({stop_code}) from cache -> {len(connections)} connections (tiempo: {elapsed:.4f} s)")
        return connections

    # === OTHER CALLS ===
    async def get_stops_by_name(self, stop_name):
        start = time.perf_counter()
        stops = await self.get_all_stops()
        if stop_name == '':
            result = stops
        result = self.fuzzy_search(query=stop_name, items=stops, key=lambda s: s.name)
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_stops_by_name({stop_name}) -> {len(result)} stops (tiempo: {elapsed:.4f} s)")
        return result

    async def get_line_by_id(self, line_id) -> TramLine:
        start = time.perf_counter()
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.code) == str(line_id)), None)
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line} (tiempo: {elapsed:.4f} s)")
        return line

    async def get_stop_by_id(self, stop_id) -> TramStation:
        start = time.perf_counter()
        stops = await self.get_all_stops()
        stop = next((s for s in stops if str(s.id) == str(stop_id)), None)
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_stop_by_id({stop_id}) -> {stop} (tiempo: {elapsed:.4f} s)")
        return stop

    async def get_stop_by_code(self, stop_code) -> TramStation:
        start = time.perf_counter()
        stops = await self.get_all_stops()
        stop = next((s for s in stops if str(s.code) == str(stop_code)), None)
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_stop_by_code({stop_code}) -> {stop} (tiempo: {elapsed:.4f} s)")
        return stop
