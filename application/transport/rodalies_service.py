from collections import defaultdict
from typing import List
from domain.common.alert import Alert
from domain.rodalies import RodaliesLine, RodaliesStation
from domain import LineRoute
from domain.transport_type import TransportType
from providers.api import RodaliesApiService
from providers.manager import LanguageManager, UserDataManager
from providers.helpers import logger

from application.cache_service import CacheService
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
        static_key = "rodalies_lines_static"
        alerts_key = "rodalies_lines_alerts"

        cached_lines = await self._get_from_cache_or_data(static_key, None, cache_ttl=3600*24)
        cached_alerts = await self._get_from_cache_or_data(alerts_key, None, cache_ttl=3600)

        # Lines cache already exist, update only alerts
        if cached_lines is not None and cached_lines:
            if cached_alerts:
                for line in cached_lines:
                    line_alerts = cached_alerts.get(line.name, [])
                    line.has_alerts = any(line_alerts)
                    line.alerts = line_alerts
            return cached_lines
        
        # No lines and no alerts in cache
        lines = await self.rodalies_api_service.get_lines()
        api_alerts = await self.rodalies_api_service.get_global_alerts()
        alerts = [Alert.map_from_rodalies_alert(alert) for alert in api_alerts]

        result = defaultdict(list)
        for alert in alerts:
            self.user_data_manager.register_alert(TransportType.RODALIES, alert)
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

        return lines
    
    async def get_all_stations(self) -> List[RodaliesStation]:
        lines = await self.get_all_lines()
        stations = []
        for line in lines:
            line_stations = await self.get_stations_by_line(line.id)
            for s in line_stations:
                s = RodaliesStation.update_line_info(s, line)
            stations += line_stations

        return await self._get_from_cache_or_data(
            "rodalies_stations",
            stations,
            cache_ttl=3600*24
        )   
    
    async def get_station_routes(self, station_id, line_id):
        routes = await self._get_from_cache_or_api(
            f"rodalies_station_{station_id}_routes",
            lambda: self.rodalies_api_service.get_next_trains_at_station(station_id, line_id),
            cache_ttl=10
        )
        return "\n\n".join(LineRoute.scheduled_list(route, with_arrival_date=False) for route in routes)
    
    async def get_line_by_id(self, line_id: str) -> RodaliesLine:
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.id) == str(line_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line}")
        return line
    
    # === OTHER CALLS ===
    async def get_stations_by_line(self, line_id) -> List[RodaliesStation]:
        """
        Retrieve stations for a specific rodalies line.
        """
        line = await self.get_line_by_id(line_id)      
        return line.stations
    
    async def get_stations_by_name(self, station_name) -> List[RodaliesStation]:
        stations = await self.get_all_stations()
        return self.fuzzy_search(
            query=station_name,
            items=stations,
            key=lambda station: station.name
        )
    
    async def get_station_by_id(self, station_id, line_id) -> RodaliesStation:
        """
        Retrieve a station by its code.
        """
        stops = await self.get_stations_by_line(line_id)
        stop = next((s for s in stops if str(s.id) == str(station_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_station_by_id({station_id}, line {line_id}) -> {stop}")
        return stop