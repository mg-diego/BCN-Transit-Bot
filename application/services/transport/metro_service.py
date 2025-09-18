import asyncio
from collections import defaultdict
from time import time
from typing import List
import time

from domain import LineRoute
from domain.common.line import Line
from domain.common.station import Station
from domain.metro import MetroLine, MetroStation, MetroAccess
from domain.common.alert import Alert
from domain.transport_type import TransportType
from providers.api import TmbApiService
from providers.helpers.utils import Utils
from providers.manager import LanguageManager
from providers.helpers import logger

from application.services.cache_service import CacheService
from providers.manager.user_data_manager import UserDataManager
from .service_base import ServiceBase

class MetroService(ServiceBase):
    """
    Service to interact with Metro data via TmbApiService, with optional caching.
    """

    def __init__(self, tmb_api_service: TmbApiService, language_manager: LanguageManager,
                 cache_service: CacheService = None, user_data_manager: UserDataManager = None):
        super().__init__(cache_service)
        self.tmb_api_service = tmb_api_service
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager
        logger.info(f"[{self.__class__.__name__}] MetroService initialized")

    # ===== CACHE CALLS ====
    async def get_all_lines(self) -> List[MetroLine]:
        start = time.perf_counter()
        static_key = "metro_lines_static"
        alerts_key = "metro_lines_alerts"

        cached_lines, cached_alerts = await asyncio.gather(
            self._get_from_cache_or_data(static_key, None, cache_ttl=3600*24*7),
            self._get_from_cache_or_data(alerts_key, None, cache_ttl=3600)
        )

        if cached_lines is not None and cached_lines:
            if cached_alerts:
                for line in cached_lines:
                    line_alerts = cached_alerts.get(line.name, [])
                    line.has_alerts = any(line_alerts)
                    line.alerts = line_alerts
            elapsed = time.perf_counter() - start
            logger.info(f"[{self.__class__.__name__}] get_all_lines() -> cached ({elapsed:.4f} s)")
            return cached_lines

        lines, api_alerts = await asyncio.gather(
            self.tmb_api_service.get_metro_lines(),
            self.tmb_api_service.get_global_alerts(TransportType.METRO)
        )
        alerts = [Alert.map_from_metro_alert(alert) for alert in api_alerts]

        result = defaultdict(list)
        for alert in alerts:
            self.user_data_manager.register_alert(TransportType.METRO, alert)
            seen_lines = set()
            for entity in alert.affected_entities:
                if entity.line_name and entity.line_name not in seen_lines:
                    result[entity.line_name].append(alert)
                    seen_lines.add(entity.line_name)

        alerts_dict = dict(result)

        for line in lines:
            line_alerts = alerts_dict.get(line.name, [])
            line.has_alerts = any(line_alerts)
            line.alerts = line_alerts

        await self._get_from_cache_or_data(static_key, lines, cache_ttl=3600*24*7)
        await self._get_from_cache_or_data(alerts_key, alerts_dict, cache_ttl=3600)

        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_all_lines() -> {len(lines)} lines ({elapsed:.4f} s)")
        return sorted(lines, key=Utils.sort_lines)

    async def get_all_stations(self) -> List[MetroStation]:
        start = time.perf_counter()
        static_stations = await self.cache_service.get("metro_stations_static")
        alerts_by_station = await self.cache_service.get("metro_stations_alerts")

        if not static_stations and not alerts_by_station:
            static_stations, alerts_by_station = await asyncio.gather(
                self._build_and_cache_static_stations(),
                self._build_and_cache_station_alerts()
            )
        elif not static_stations:
            static_stations = await self._build_and_cache_static_stations()
        elif not alerts_by_station:
            alerts_by_station = await self._build_and_cache_station_alerts()

        for station in static_stations:
            station_alerts = alerts_by_station.get(station.code, [])
            station.has_alerts = any(station_alerts)
            station.alerts = station_alerts if any(station_alerts) else []

        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_all_stations() -> {len(static_stations)} stations ({elapsed:.4f} s)")
        return static_stations

    async def get_stations_by_line(self, line_code) -> List[MetroStation]:
        start = time.perf_counter()
        cache_key = f"metro_line_{line_code}_stations"
        cached_stations = await self._get_from_cache_or_data(cache_key, None, cache_ttl=3600*24*7)
        if cached_stations:
            elapsed = time.perf_counter() - start
            logger.info(f"[{self.__class__.__name__}] get_stations_by_line({line_code}) -> cached ({elapsed:.4f} s)")
            return cached_stations

        line = await self.get_line_by_code(line_code)
        api_stations = await self.tmb_api_service.get_stations_by_metro_line(line_code)

        semaphore_connections = asyncio.Semaphore(10)

        async def process_station(api_station):
            async with semaphore_connections:
                connections = await self.tmb_api_service.get_station_connections(api_station.code)
                station = MetroStation.update_metro_station_with_line_info(api_station, line)
                station = MetroStation.update_metro_station_with_connections(station, connections)
                return station

        line_stations = await asyncio.gather(*[process_station(s) for s in api_stations])
        result = await self._get_from_cache_or_data(cache_key, line_stations, cache_ttl=3600*24*7)

        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_stations_by_line({line_id}) -> {len(result)} stations ({elapsed:.4f} s)")
        return result

    async def get_station_accesses(self, group_code_id) -> List[MetroAccess]:
        start = time.perf_counter()
        data = await self._get_from_cache_or_api(
            f"metro_station_{group_code_id}_accesses",
            lambda: self.tmb_api_service.get_metro_station_accesses(group_code_id),
            cache_ttl=3600*24
        )
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_station_accesses({group_code_id}) -> {len(data)} accesses ({elapsed:.4f} s)")
        return data

    async def get_station_routes(self, station_code) -> List[LineRoute]:
        start = time.perf_counter()
        routes = await self._get_from_cache_or_api(
            f"metro_station_{station_code}_routes",
            lambda: self.tmb_api_service.get_next_metro_at_station(station_code),
            cache_ttl=10
        )
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_station_routes({station_code}) -> {len(routes)} routes ({elapsed:.4f} s)")
        return routes

    async def get_stations_by_name(self, station_name) -> List[MetroStation]:
        start = time.perf_counter()
        stations = await self.get_all_stations()

        if station_name != '':
            result = self.fuzzy_search(
                query=station_name,
                items=stations,
                key=lambda station: station.name
            )
        else:
            result = stations
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_stations_by_name({station_name}) -> {len(result)} matches ({elapsed:.4f} s)")
        return result

    async def get_station_by_code(self, station_code) -> MetroStation:
        start = time.perf_counter()
        stations = await self.get_all_stations()
        filtered_stations = [station for station in stations if int(station_code) == int(station.code)]
        station = filtered_stations[0] if filtered_stations else None
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_station_by_id({station_code}) -> {station} ({elapsed:.4f} s)")
        return station

    async def get_line_by_code(self, line_code) -> MetroLine:
        start = time.perf_counter()
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.code) == str(line_code)), None)
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_line_by_id({line_code}) -> {line} ({elapsed:.4f} s)")
        return line

    async def get_line_by_name(self, line_name):
        start = time.perf_counter()
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.name) == str(line_name)), None)
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] get_line_by_name({line_name}) -> {line} ({elapsed:.4f} s)")
        return line

    async def _build_and_cache_static_stations(self) -> List[MetroStation]:
        start = time.perf_counter()
        lines = await self.get_all_lines()
        stations = []

        semaphore_lines = asyncio.Semaphore(5)
        semaphore_connections = asyncio.Semaphore(10)

        async def process_station(api_station: Station, line: Line):
            async with semaphore_connections:
                connections = await self.tmb_api_service.get_station_connections(api_station.code)
                station = MetroStation.update_metro_station_with_line_info(api_station, line)
                station = MetroStation.update_metro_station_with_connections(station, connections)
                return station

        async def process_line(line):
            async with semaphore_lines:
                line_stations = await self.tmb_api_service.get_stations_by_metro_line(line.code)
            processed_stations = await asyncio.gather(*[process_station(s, line) for s in line_stations])
            return processed_stations

        results = await asyncio.gather(*[process_line(line) for line in lines])

        for line_stations in results:
            stations.extend(line_stations)

        await self.cache_service.set("metro_stations_static", stations, ttl=3600*24*7)
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] _build_and_cache_static_stations() -> {len(stations)} stations ({elapsed:.4f} s)")
        return stations

    async def _build_and_cache_station_alerts(self):
        start = time.perf_counter()
        station_alerts = defaultdict(list)
        lines = await self.get_all_lines()
        alert_lines = [line for line in lines if line.has_alerts]

        semaphore = asyncio.Semaphore(10)

        async def process_line(line):
            async with semaphore:
                stations = await self.get_stations_by_line(line.code)
            return [(st.code, st.alerts) for st in stations]

        results = await asyncio.gather(*(process_line(line) for line in alert_lines))

        for station_list in results:
            for code, alerts in station_list:
                station_alerts[code].extend(alerts)

        alerts_dict = dict(station_alerts)
        await self.cache_service.set("metro_stations_alerts", alerts_dict, ttl=3600)
        elapsed = time.perf_counter() - start
        logger.info(f"[{self.__class__.__name__}] _build_and_cache_station_alerts() -> {len(alerts_dict)} stations with alerts ({elapsed:.4f} s)")
        return alerts_dict
