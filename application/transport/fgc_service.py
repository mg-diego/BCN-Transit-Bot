import asyncio
from typing import List
import json

from domain.fgc import FgcLine, FgcStation
from domain import NextTrip, LineRoute, normalize_to_seconds
from providers.api import FgcApiService
from providers.manager import LanguageManager
from providers.helpers import logger

from application.cache_service import CacheService
from providers.manager.user_data_manager import UserDataManager
from domain.transport_type import TransportType
from .service_base import ServiceBase

class FgcService(ServiceBase):
    """
    Service to interact with Metro data via TmbApiService, with optional caching.
    """

    def __init__(self, fgc_api_service: FgcApiService, language_manager: LanguageManager, cache_service: CacheService = None, user_data_manager: UserDataManager = None):
        super().__init__(cache_service)
        self.fgc_api_service = fgc_api_service
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager
        logger.info(f"[{self.__class__.__name__}] FgcService initialized")

    # ===== CACHE CALLS ====
    async def get_all_lines(self) -> List[FgcLine]:
        return await self._get_from_cache_or_api(
            "fgc_lines",
            lambda: self.fgc_api_service.get_all_lines(),
            cache_ttl=3600*24
        )
    
    async def get_all_stations(self) -> List[FgcStation]:
        fgc_stations_key = "fgc_stations"
        cached_stations = await self._get_from_cache_or_data(fgc_stations_key, None, cache_ttl=3600*24)

        if cached_stations is not None:
            return cached_stations

        lines = await self.get_all_lines()
        stations = []

        # Limita concurrencia: ajusta según capacidad de la API
        semaphore_lines = asyncio.Semaphore(5)     # Para get_stations_by_line
        semaphore_near = asyncio.Semaphore(10)     # Para get_near_stations

        async def process_station(line_station, line):
            async with semaphore_near:
                line_station = FgcStation.update_line_info(line_station, line)
                moute_station = await self.fgc_api_service.get_near_stations(line_station.latitude, line_station.longitude)
                if moute_station:
                    line_station.moute_id = moute_station[0].get('id')
                return line_station

        async def process_line(line):
            async with semaphore_lines:
                line_stations = await self.fgc_api_service.get_stations_by_line(line.id)

            # Procesa todas las estaciones en paralelo
            processed_stations = await asyncio.gather(*[process_station(s, line) for s in line_stations])
            return processed_stations

        # Procesa todas las líneas en paralelo
        results = await asyncio.gather(*[process_line(line) for line in lines])

        for line_stations in results:
            stations.extend(line_stations)

        logger.warning(f"The following FGC stations where not found:\n {[s for s in stations if s.moute_id is None]}")
        return await self._get_from_cache_or_data(fgc_stations_key, stations, cache_ttl=3600*24)

    
    async def get_stations_by_line(self, line_id) -> List[FgcStation]:
        stations = await self.get_all_stations()
        return [s for s in stations if s.line_id == line_id]
    
    async def get_stations_by_name(self, station_name) -> List[FgcStation]:
        stations = await self.get_all_stations()
        if station_name == '':
            return stations
        return self.fuzzy_search(
            query=station_name,
            items=stations,
            key=lambda station: station.name
        )
    
    async def get_station_routes(self, station_name, moute_id, line_name):
        routes = await self._get_from_cache_or_data(
            f"fgc_station_{station_name}_routes",
            None,
            cache_ttl=30
        )

        if routes is None:
            if moute_id != None:
                raw_routes = await self.fgc_api_service.get_moute_next_departures(moute_id, line_name)

                routes = []
                for direction, trips in raw_routes.items():
                    nextFgc = [
                        NextTrip(
                            id='',
                            arrival_time=normalize_to_seconds(int(trip.get('departure_time'))),
                        )
                        for trip in trips
                    ]
                    routes.append(LineRoute(
                        destination=direction,
                        next_trips=nextFgc,
                        line_name=line_name,
                        line_id=line_name,
                        line_type=TransportType.FGC,
                        color=None,
                        route_id=line_name
                    ))
            else:
                raw_routes = await self.fgc_api_service.get_next_departures(station_name, line_name)

                routes =  []
                for direction, trips in raw_routes.items():
                    nextFgc = [
                        NextTrip(
                            id=trip.get('trip_id'),
                            arrival_time=normalize_to_seconds(trip.get('departure_time'))
                        )
                        for trip in trips
                    ]
                    routes.append(LineRoute(
                        destination=direction,
                        next_trips=nextFgc,
                        line_name=line_name,
                        line_id=line_name,
                        line_type=TransportType.FGC,
                        color=None,
                        route_id=line_name
                    ))

            routes = await self._get_from_cache_or_data(
                f"fgc_station_{station_name}_routes",
                routes,
                cache_ttl=30
            )

        return "\n\n".join(LineRoute.scheduled_list(route) for route in routes)
    
    async def get_station_by_id(self, station_id, line_id) -> FgcStation:
        """
        Retrieve a station by its code.
        """
        stations = await self.get_stations_by_line(line_id)
        station = next((s for s in stations if str(s.id) == str(station_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_station_by_id({station_id}, line {line_id}) -> {station}")
        return station
    
    async def get_line_by_id(self, line_id) -> FgcLine:
        """
        Retrieve a station by its code.
        """
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.id) == str(line_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line}")
        return line
