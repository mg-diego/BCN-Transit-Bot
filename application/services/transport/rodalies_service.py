from collections import defaultdict
from typing import List
import time
from domain.common.alert import Alert
from domain.common.connections import Connections
from domain.rodalies import RodaliesLine, RodaliesStation
from domain import LineRoute
from domain.transport_type import TransportType
from providers.api import RodaliesApiService
from providers.manager import LanguageManager, UserDataManager
from providers.helpers import logger

from application.services.cache_service import CacheService
from .service_base import ServiceBase


class RodaliesService(ServiceBase):

    def __init__(self, rodalies_api_service: RodaliesApiService, language_manager: LanguageManager, cache_service: CacheService = None, user_data_manager: UserDataManager = None):
        super().__init__(cache_service)
        self.rodalies_api_service = rodalies_api_service
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager        
        logger.info(f"[{self.__class__.__name__}] RodaliesService initialized")

    # === CACHE CALLS ===
    async def get_all_lines(self) -> List[RodaliesLine]:
        start = time.perf_counter()
        static_key = "rodalies_lines_static"
        alerts_key = "rodalies_lines_alerts"

        cached_lines = await self._get_from_cache_or_data(static_key, None, cache_ttl=3600*24)
        cached_alerts = await self._get_from_cache_or_data(alerts_key, None, cache_ttl=3600)

        if cached_lines is not None and cached_lines:
            if cached_alerts:
                for line in cached_lines:
                    line_alerts = cached_alerts.get(line.name, [])
                    line.has_alerts = any(line_alerts)
                    line.alerts = line_alerts
            elapsed = (time.perf_counter() - start)
            logger.info(f"[{self.__class__.__name__}] get_all_lines (cache hit) ejecutado en {elapsed:.4f} s")
            return cached_lines

        # No lines and no alerts in cache
        lines = await self.rodalies_api_service.get_lines()
        api_alerts = await self.rodalies_api_service.get_global_alerts()
        alerts = [Alert.map_from_rodalies_alert(alert) for alert in api_alerts]

        result = defaultdict(list)
        for alert in alerts:
            await self.user_data_manager.register_alert(TransportType.RODALIES, alert)
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

        await self._get_from_cache_or_data(static_key, lines, cache_ttl=3600*24)
        await self._get_from_cache_or_data(alerts_key, alerts_dict, cache_ttl=3600)

        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_all_lines ejecutado en {elapsed:.4f} s")
        return lines

    async def get_all_stations(self) -> List[RodaliesStation]:
        start = time.perf_counter()
        stations = await self.cache_service.get("rodalies_stations")

        if not stations:
            lines = await self.get_all_lines()
            stations = []
            for line in lines:
                line_stations = await self.get_stations_by_line(line.id)
                for s in line_stations:
                    s = RodaliesStation.update_line_info(s, line)
                stations += line_stations

            await self.cache_service.set("rodalies_stations", stations, ttl=3600*24)

        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_all_stations ejecutado en {elapsed:.4f} s")
        return stations

    async def get_station_routes(self, station_code) -> List[LineRoute]:
        start = time.perf_counter()
        station = await self.get_station_by_code(station_code)
        routes = await self._get_from_cache_or_api(
            f"rodalies_station_{station_code}_routes",
            lambda: self.rodalies_api_service.get_next_trains_at_station(station.id),
            cache_ttl=10
        )
        
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_station_routes({station_code}) ejecutado en {elapsed:.4f} s")
        return routes

    async def get_line_by_id(self, line_id: str) -> RodaliesLine:
        start = time.perf_counter()
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.id) == str(line_id)), None)
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line} ejecutado en {elapsed:.4f} s")
        return line

    # === OTHER CALLS ===
    async def get_stations_by_line(self, line_id) -> List[RodaliesStation]:
        start = time.perf_counter()
        line = await self.get_line_by_id(line_id)      
        result = line.stations
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_stations_by_line({line_id}) ejecutado en {elapsed:.4f} s")
        return result

    async def get_stations_by_name(self, station_name) -> List[RodaliesStation]:
        start = time.perf_counter()
        stations = await self.get_all_stations()
        if station_name == '':
            elapsed = (time.perf_counter() - start)
            logger.info(f"[{self.__class__.__name__}] get_stations_by_name(empty) ejecutado en {elapsed:.4f} s")
            return stations
        result = self.fuzzy_search(
            query=station_name,
            items=stations,
            key=lambda station: station.name
        )
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_stations_by_name({station_name}) ejecutado en {elapsed:.4f} s")
        return result

    async def get_station_by_id(self, station_id) -> RodaliesStation:
        start = time.perf_counter()
        stops = await self.get_all_stations()
        stop = next((s for s in stops if str(s.id) == str(station_id)), None)
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_station_by_id({station_id}) -> {stop} ejecutado en {elapsed:.4f} s")
        return stop
    
    async def get_station_by_code(self, station_code) -> RodaliesStation:
        start = time.perf_counter()
        stops = await self.get_all_stations()
        stop = next((s for s in stops if str(s.id) == str(station_code)), None)
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_station_by_code({station_code}) -> {stop} ejecutado en {elapsed:.4f} s")  
        return stop
    
    async def get_rodalies_station_connections(self, station_code) -> Connections:
        start = time.perf_counter()
        connections = await self.cache_service.get(f"rodalies_station_connections_{station_code}")
        if connections:
            elapsed = (time.perf_counter() - start)
            logger.info(f"[{self.__class__.__name__}] get_rodalies_station_connections({station_code}) from cache -> {len(connections)} connections (tiempo: {elapsed:.4f} s)")
            return connections
        
        same_stops = [s for s in await self.get_all_stations() if s.code == station_code]
        connections = [RodaliesLine.create_rodalies_connection(s.line_id, s.line_code, s.line_name, s.line_description, '', '', s.line_color) for s in same_stops]
        await self.cache_service.set(f"rodalies_station_connections_{station_code}", connections, ttl=3600*24)

        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_rodalies_station_connections({station_code}) from cache -> {len(connections)} connections (tiempo: {elapsed:.4f} s)")
        return connections
