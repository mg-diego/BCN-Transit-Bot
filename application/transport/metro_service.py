from collections import defaultdict
from typing import List
import json

from domain.metro import MetroLine, MetroStation, MetroAccess, update_metro_station_with_line_info, update_metro_station_with_connections
from domain.common.alert import Alert
from domain.transport_type import TransportType
from providers.api import TmbApiService
from providers.manager import LanguageManager
from providers.helpers import logger

from application.cache_service import CacheService
from providers.manager.user_data_manager import UserDataManager
from .service_base import ServiceBase

class MetroService(ServiceBase):
    """
    Service to interact with Metro data via TmbApiService, with optional caching.
    """

    def __init__(self, tmb_api_service: TmbApiService, language_manager: LanguageManager, cache_service: CacheService = None, user_data_manager: UserDataManager = None):
        super().__init__(cache_service)
        self.tmb_api_service = tmb_api_service
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager
        logger.info(f"[{self.__class__.__name__}] MetroService initialized")


    # ===== CACHE CALLS ====
    async def get_all_lines(self) -> List[MetroLine]:
        static_key = "metro_lines_static"
        alerts_key = "metro_lines_alerts"

        cached_lines = await self._get_from_cache_or_data(static_key, None, cache_ttl=3600*24)
        cached_alerts = await self._get_from_cache_or_data(alerts_key, None, cache_ttl=3600)

        # Lines cache already exist, update only alerts
        if cached_lines is not None and cached_lines:
            if cached_alerts:
                for line in cached_lines:
                    line_alerts = cached_alerts.get(line.ORIGINAL_NOM_LINIA, [])
                    line.has_alerts = any(line_alerts)
                    line.alerts = line_alerts
            return cached_lines

        # No lines and no alerts in cache
        lines = await self.tmb_api_service.get_metro_lines()
        api_alerts = await self.tmb_api_service.get_global_alerts(TransportType.METRO)
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
            line_alerts = alerts_dict.get(line.ORIGINAL_NOM_LINIA, [])
            line.has_alerts = any(line_alerts)
            line.alerts = line_alerts

        await self._get_from_cache_or_data(static_key, lines, cache_ttl=3600*24)
        await self._get_from_cache_or_data(alerts_key, alerts_dict, cache_ttl=3600)

        return lines
    
    async def get_all_stations(self) -> List[MetroStation]:
        static_stations = await self.cache_service.get("metro_stations_static")
        alerts_by_station = await self.cache_service.get("metro_stations_alerts")

        if not static_stations:
            static_stations = await self._build_and_cache_static_stations()
        if not alerts_by_station:
            alerts_by_station = await self._build_and_cache_station_alerts()

        for station in static_stations:
            station_alerts = alerts_by_station.get(station.CODI_ESTACIO, [])
            station.has_alerts = any(station_alerts)
            station.alerts = station_alerts if any(station_alerts) else []

        return static_stations
            
    async def get_stations_by_line(self, line_id) -> List[MetroStation]:
        cache_key = f"metro_line_{line_id}_stations"
        cached_stations = await self._get_from_cache_or_data(cache_key, None, cache_ttl=3600*24)
        if cached_stations:
            return cached_stations

        line = await self.get_line_by_id(line_id)
        line_stations = []
        api_stations = await self.tmb_api_service.get_stations_by_metro_line(line_id)
        for api_station in api_stations:
            connections = await self.tmb_api_service.get_station_connections(api_station.CODI_ESTACIO)
            station = update_metro_station_with_line_info(api_station, line)
            station = update_metro_station_with_connections(station, connections)
            line_stations.append(station)

        return await self._get_from_cache_or_data(cache_key, line_stations, cache_ttl=3600*24)


    async def get_station_accesses(self, group_code_id) -> List[MetroAccess]:
        return await self._get_from_cache_or_api(
            f"metro_station_{group_code_id}_accesses",
            lambda: self.tmb_api_service.get_metro_station_accesses(group_code_id),
            cache_ttl=3600*24
        )

    async def get_station_routes(self, metro_station_id):
        routes = await self._get_from_cache_or_api(
            f"metro_station_{metro_station_id}_routes",
            lambda: self.tmb_api_service.get_next_metro_at_station(metro_station_id),
            cache_ttl=10
        )
        return "\n\n".join(str(route) for route in routes)
    
    # ===== OTHER CALLS ====
    async def get_stations_by_name(self, station_name) -> List[MetroStation]:
        stations = await self.get_all_stations()
        logger.debug(f"[{self.__class__.__name__}] get_stations_by_name({station_name})")
        return self.fuzzy_search(
            query=station_name,
            items=stations,
            key=lambda stop: stop.NOM_ESTACIO
        )

    async def get_station_by_id(self, station_id) -> MetroStation:        
        stations = await self.get_all_stations()
        filtered_stations = [
            station for station in stations
            if int(station_id) == int(station.CODI_ESTACIO)
        ]

        station = filtered_stations[0] if any(filtered_stations) else None
        logger.debug(f"[{self.__class__.__name__}] get_station_by_id({station_id}) -> {station}")
        return station

    async def get_line_by_id(self, line_id) -> MetroLine:
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.CODI_LINIA) == str(line_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line}")
        return line

    async def get_line_by_name(self, line_name):
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.ORIGINAL_NOM_LINIA) == str(line_name)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_name({line_name}) -> {line}")
        return line
    
    async def _build_and_cache_static_stations(self):
        lines = await self.get_all_lines()
        stations = []

        for line in lines:
            line_stations = await self.tmb_api_service.get_stations_by_metro_line(line.CODI_LINIA)
            for api_station in line_stations:
                connections = await self.tmb_api_service.get_station_connections(api_station.CODI_ESTACIO)
                station = update_metro_station_with_line_info(api_station, line)
                station = update_metro_station_with_connections(station, connections)
                stations.append(station)

        await self.cache_service.set("metro_stations_static", stations, ttl=3600*24)
        return stations
    
    async def _build_and_cache_station_alerts(self):
        station_alerts = defaultdict(list)

        lines = await self.get_all_lines()
        for line in lines:
            if not line.has_alerts:
                continue

            stations = await self.get_stations_by_line(line.CODI_LINIA)
            for station in stations:
                station_alerts[station.CODI_ESTACIO].extend(station.alerts)

        alerts_dict = dict(station_alerts)
        await self.cache_service.set("metro_stations_alerts", alerts_dict, ttl=3600)
        return alerts_dict