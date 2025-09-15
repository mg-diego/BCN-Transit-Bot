import asyncio
import time
from collections import defaultdict
from typing import List

from domain import LineRoute
from domain.common.alert import Alert
from domain.transport_type import TransportType
from providers.api.tmb_api_service import TmbApiService

from domain.bus import BusLine, BusStop
from providers.helpers import logger
from providers.manager import UserDataManager, LanguageManager

from .service_base import ServiceBase
from application.cache_service import CacheService


class BusService(ServiceBase):
    """
    Service to interact with Bus data via TmbApiService, with optional caching.
    """

    def __init__(self, tmb_api_service: TmbApiService,
                 cache_service: CacheService = None,
                 user_data_manager: UserDataManager = None,
                 language_manager: LanguageManager = None):
        super().__init__(cache_service)
        self.tmb_api_service = tmb_api_service
        self.user_data_manager = user_data_manager
        self.language_manager = language_manager
        logger.info(f"[{self.__class__.__name__}] BusService initialized")

    # === CACHE CALLS ===
    async def get_all_lines(self) -> List[BusLine]:
        start = time.perf_counter()
        static_key = "bus_lines_static"
        alerts_key = "bus_lines_alerts"

        cached_lines, cached_alerts = await asyncio.gather(
            self._get_from_cache_or_data(static_key, None, cache_ttl=3600*24),
            self._get_from_cache_or_data(alerts_key, None, cache_ttl=3600)
        )

        if cached_lines is not None and cached_lines:
            if cached_alerts:
                for line in cached_lines:
                    line_alerts = cached_alerts.get(line.ORIGINAL_NOM_LINIA, [])
                    line.has_alerts = any(line_alerts)
                    line.alerts = line_alerts
            elapsed = time.perf_counter() - start
            logger.info(f"[{self.__class__.__name__}] get_all_lines() -> cached ({elapsed:.4f} s)")
            return cached_lines

        lines, api_alerts = await asyncio.gather(
            self.tmb_api_service.get_bus_lines(),
            self.tmb_api_service.get_global_alerts(TransportType.BUS)
        )
        alerts = [Alert.map_from_bus_alert(alert) for alert in api_alerts]

        result = defaultdict(list)
        for alert in alerts:
            self.user_data_manager.register_alert(TransportType.BUS, alert)
            seen_lines = set()
            for entity in alert.affected_entities:
                if entity.line_name and entity.line_name not in seen_lines:
                    result[entity.line_name].append(alert)
                    seen_lines.add(entity.line_name)
        alerts_dict = dict(result)

        for line in lines:
            line_alerts = alerts_dict.get(line.ORIGINAL_NOM_LINIA, [])
            line.has_alerts = any(line_alerts)
            line.alerts = line_alerts

        await self._get_from_cache_or_data(static_key, lines, cache_ttl=3600*24)
        await self._get_from_cache_or_data(alerts_key, alerts_dict, cache_ttl=3600)

        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_all_lines() -> {len(lines)} lines ({elapsed:.4f} s)")
        return lines

    async def get_all_stops(self) -> List[BusStop]:
        start = time.perf_counter()
        static_stops = await self.cache_service.get("bus_stops_static")
        alerts_by_stop = await self.cache_service.get("bus_stops_alerts")

        if not static_stops and not alerts_by_stop:
            static_stops, alerts_by_stop = await asyncio.gather(
                self._build_and_cache_static_stops(),
                self._build_and_cache_stop_alerts()
            )
        elif not static_stops:
            static_stops = await self._build_and_cache_static_stops()
        elif not alerts_by_stop:
            alerts_by_stop = await self._build_and_cache_stop_alerts()

        for stop in static_stops:
            stop_alerts = alerts_by_stop.get(stop.code, [])
            stop.has_alerts = any(stop_alerts)
            stop.alerts = stop_alerts if any(stop_alerts) else []

        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_all_stops() -> {len(static_stops)} stops ({elapsed:.4f} s)")
        return static_stops

    async def get_stops_by_line(self, line_id) -> List[BusStop]:
        start = time.perf_counter()
        cache_key = f"bus_line_{line_id}_stops"
        cached_stations = await self._get_from_cache_or_data(cache_key, None, cache_ttl=3600*24)
        if cached_stations is not None and cached_stations:
            elapsed = time.perf_counter() - start
            logger.info(f"[{self.__class__.__name__}] get_stops_by_line({line_id}) -> cached ({elapsed:.4f} s)")
            return cached_stations

        line = await self.get_line_by_id(line_id)
        api_stops = await self.tmb_api_service.get_bus_line_stops(line_id)

        line_stops = [BusStop.update_bus_stop_with_line_info(s, line) for s in api_stops]
        result = await self._get_from_cache_or_data(cache_key, line_stops, cache_ttl=3600*24)

        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_stops_by_line({line_id}) -> {len(result)} stops ({elapsed:.4f} s)")
        return result

    async def get_stop_routes(self, stop_id: str) -> str:
        start = time.perf_counter()
        routes = await self._get_from_cache_or_api(
            f"bus_stop_{stop_id}_routes",
            lambda: self.tmb_api_service.get_next_bus_at_stop(stop_id),
            cache_ttl=10
        )
        msg = "\n\n".join(
            LineRoute.simple_list(route, arriving_threshold=60,
                                  default_msg=self.language_manager.t('no.departures.found'))
            for route in routes
        )
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_stop_routes({stop_id}) -> {len(routes)} routes ({elapsed:.4f} s)")
        return msg

    # === OTHER CALLS ===
    async def get_stops_by_name(self, stop_name) -> List[BusLine]:
        start = time.perf_counter()
        stops = await self.get_all_stops()

        if stop_name != '':
            result = self.fuzzy_search(
                query=stop_name,
                items=stops,
                key=lambda stop: stop.name
            )
        else:
            result = stops
            
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_stops_by_name({stop_name}) -> {len(result)} matches ({elapsed:.4f} s)")
        return result

    async def get_line_by_id(self, line_id) -> BusLine:
        start = time.perf_counter()
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.CODI_LINIA) == str(line_id)), None)
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line} ({elapsed:.4f} s)")
        return line

    async def get_lines_by_category(self, bus_category: str):
        start = time.perf_counter()
        lines = await self.get_all_lines()
        if "-" in bus_category:
            start_cat, end_cat = bus_category.split("-")
            result = [
                line for line in lines
                if int(start_cat) <= int(line.CODI_LINIA) <= int(end_cat)
                and line.ORIGINAL_NOM_LINIA.isdigit()
            ]
        else:
            result = [
                line for line in lines
                if bus_category == line.NOM_FAMILIA
            ]
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_lines_by_category({bus_category}) -> {len(result)} lines ({elapsed:.4f} s)")
        return result

    async def get_stop_by_id(self, stop_id) -> BusStop:
        start = time.perf_counter()
        stops = await self.get_all_stops()
        filtered_stops = [
            stop for stop in stops
            if int(stop_id) == int(stop.code)
        ]
        result = next((bs for bs in filtered_stops if bs.has_alerts),
                      filtered_stops[0] if filtered_stops else None)
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_stop_by_id({stop_id}) -> {result} ({elapsed:.4f} s)")
        return result

    async def _build_and_cache_static_stops(self) -> List[BusStop]:
        start = time.perf_counter()
        stops = []
        lines = await self.get_all_lines()

        semaphore_lines = asyncio.Semaphore(5)

        async def process_line(line):
            async with semaphore_lines:
                api_stops = await self.tmb_api_service.get_bus_line_stops(line.CODI_LINIA)
            return [BusStop.update_bus_stop_with_line_info(s, line) for s in api_stops]

        results = await asyncio.gather(*[process_line(line) for line in lines])
        for line_stops in results:
            stops.extend(line_stops)

        await self.cache_service.set("bus_stops_static", stops, ttl=3600 * 24)
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] _build_and_cache_static_stops() -> {len(stops)} stops ({elapsed:.4f} s)")
        return stops

    async def _build_and_cache_stop_alerts(self) -> dict:
        start = time.perf_counter()
        alerts_by_stop = defaultdict(list)
        lines = await self.get_all_lines()
        alert_lines = [line for line in lines if line.has_alerts]

        semaphore = asyncio.Semaphore(10)

        async def process_line(line):
            async with semaphore:
                stops = await self.get_stops_by_line(line.CODI_LINIA)
            return [(stop.code, stop.alerts) for stop in stops]

        results = await asyncio.gather(*[process_line(line) for line in alert_lines])
        for stop_list in results:
            for code, alerts in stop_list:
                alerts_by_stop[code].extend(alerts)

        alerts_dict = dict(alerts_by_stop)
        await self.cache_service.set("bus_stops_alerts", alerts_dict, ttl=3600)
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] _build_and_cache_stop_alerts() -> {len(alerts_dict)} stops with alerts ({elapsed:.4f} s)")
        return alerts_dict
