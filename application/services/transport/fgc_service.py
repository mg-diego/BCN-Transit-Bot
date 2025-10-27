import asyncio
import time
from typing import List

from domain.common.connections import Connections
from domain.common.line import Line
from domain.fgc import FgcLine, FgcStation
from domain import NextTrip, LineRoute, normalize_to_seconds
from providers.api import FgcApiService
from providers.manager import LanguageManager
from providers.helpers import logger

from application.services.cache_service import CacheService
from providers.manager.user_data_manager import UserDataManager
from domain.transport_type import TransportType
from .service_base import ServiceBase


class FgcService(ServiceBase):
    """
    Service to interact with Metro data via TmbApiService, with optional caching.
    """

    def __init__(
        self,
        fgc_api_service: FgcApiService,
        language_manager: LanguageManager,
        cache_service: CacheService = None,
        user_data_manager: UserDataManager = None
    ):
        super().__init__(cache_service)
        self.fgc_api_service = fgc_api_service
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager
        logger.info(f"[{self.__class__.__name__}] FgcService initialized")

    # ===== CACHE CALLS ====
    async def get_all_lines(self) -> List[FgcLine]:
        start = time.perf_counter()
        result = await self._get_from_cache_or_api(
            "fgc_lines",
            lambda: self.fgc_api_service.get_all_lines(),
            cache_ttl=3600 * 24
        )
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_all_lines ejecutado en {elapsed:.4f} s")
        return result

    async def get_all_stations(self) -> List[FgcStation]:
        start = time.perf_counter()
        fgc_stations_key = "fgc_stations"
        cached_stations = await self._get_from_cache_or_data(
            fgc_stations_key, None, cache_ttl=3600 * 24
        )

        if cached_stations is not None:
            elapsed = (time.perf_counter() - start)
            logger.info(f"[{self.__class__.__name__}] get_all_stations (cache hit) ejecutado en {elapsed:.4f} s")
            return cached_stations

        lines = await self.get_all_lines()
        stations = []

        # Limita concurrencia: ajusta según capacidad de la API
        semaphore_lines = asyncio.Semaphore(5)   # Para get_stations_by_line
        semaphore_near = asyncio.Semaphore(10)   # Para get_near_stations

        async def process_station(line_station, line):
            async with semaphore_near:
                line_station = FgcStation.update_line_info(line_station, line)
                moute_station = await self.fgc_api_service.get_near_stations(
                    line_station.latitude, line_station.longitude
                )
                if moute_station:
                    line_station.moute_id = moute_station[0].get("id")
                return line_station

        async def process_line(line: Line):
            async with semaphore_lines:
                line_stations = await self.fgc_api_service.get_stations_by_line(line.id)
            processed_stations = await asyncio.gather(
                *[process_station(s, line) for s in line_stations]
            )
            return processed_stations

        results = await asyncio.gather(*[process_line(line) for line in lines])
        for line_stations in results:
            stations.extend(line_stations)

        logger.warning(
            f"The following FGC stations where not found:\n "
            f"{[s for s in stations if s.moute_id is None]}"
        )
        result = await self._get_from_cache_or_data(
            fgc_stations_key, stations, cache_ttl=3600 * 24
        )
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_all_stations ejecutado en {elapsed:.4f} s")
        return result

    async def get_stations_by_line(self, line_id) -> List[FgcStation]:
        start = time.perf_counter()
        stations = await self.get_all_stations()
        result = [s for s in stations if s.line_id == line_id]
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_stations_by_line({line_id}) ejecutado en {elapsed:.4f} s")
        return result

    async def get_stations_by_name(self, station_name) -> List[FgcStation]:
        start = time.perf_counter()
        stations = await self.get_all_stations()
        if station_name == "":
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

    async def get_station_routes(self, station_code) -> List[LineRoute]:
        start = time.perf_counter()
        station = await self.get_station_by_code(station_code)

        routes = await self._get_from_cache_or_data(
            f"fgc_station_{station_code}_routes",
            None,
            cache_ttl=30
        )

        if routes is None:
            if station.moute_id is not None:
                raw_routes = await self.fgc_api_service.get_moute_next_departures(station.moute_id)
                routes = []
                for line, destinations in raw_routes.items():
                    for destination, trips in destinations.items():
                        nextFgc = [
                            NextTrip(
                                id="",
                                arrival_time=normalize_to_seconds(int(trip.get("departure_time"))),
                            )
                            for trip in trips
                        ]
                        routes.append(
                            LineRoute(
                                destination=destination,
                                next_trips=nextFgc,
                                line_name=line,
                                line_id=line,
                                line_code=line,
                                line_type=TransportType.FGC,
                                color=None,
                                route_id=line,
                            )
                        )
            else:
                raw_routes = await self.fgc_api_service.get_next_departures(station.name, station.line_name)
                routes = []
                for direction, trips in raw_routes.items():
                    nextFgc = [
                        NextTrip(
                            id=trip.get("trip_id"),
                            arrival_time=normalize_to_seconds(trip.get("departure_time")),
                        )
                        for trip in trips
                    ]
                    routes.append(
                        LineRoute(
                            destination=direction,
                            next_trips=nextFgc,
                            line_name=station.line_name,
                            line_id=station.line_name,
                            line_code=station.line_name,
                            line_type=TransportType.FGC,
                            color=None,
                            route_id=station.line_name,
                        )
                    )

            routes = await self._get_from_cache_or_data(
                f"fgc_station_{station_code}_routes",
                routes,
                cache_ttl=30,
            )
        
        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_station_routes({station_code}) ejecutado en {elapsed:.4f} s")
        return routes

    async def get_station_by_id(self, station_id, line_id) -> FgcStation:
        start = time.perf_counter()
        stations = await self.get_stations_by_line(line_id)
        station = next((s for s in stations if str(s.id) == str(station_id)), None)
        elapsed = (time.perf_counter() - start)
        logger.info(
            f"[{self.__class__.__name__}] get_station_by_id({station_id}, line {line_id}) "
            f"-> {station} ejecutado en {elapsed:.4f} s"
        )
        return station
    
    async def get_station_by_code(self, station_code) -> FgcStation:
        start = time.perf_counter()
        stations = await self.get_all_stations()
        station = next((s for s in stations if str(s.code) == str(station_code)), None)
        elapsed = (time.perf_counter() - start)
        logger.info(
            f"[{self.__class__.__name__}] get_station_by_id({station_code}) "
            f"-> {station} ejecutado en {elapsed:.4f} s"
        )
        return station

    async def get_line_by_id(self, line_id) -> FgcLine:
        start = time.perf_counter()
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.id) == str(line_id)), None)
        elapsed = (time.perf_counter() - start)
        logger.info(
            f"[{self.__class__.__name__}] get_line_by_id({line_id}) "
            f"-> {line} ejecutado en {elapsed:.4f} s"
        )
        return line
    
    async def get_fgc_station_connections(self, station_code) -> Connections:
        start = time.perf_counter()
        connections = await self.cache_service.get(f"fgc_station_connections_{station_code}")
        if connections:
            elapsed = (time.perf_counter() - start)
            logger.info(f"[{self.__class__.__name__}] get_fgc_station_connections({station_code}) from cache -> {len(connections)} connections (tiempo: {elapsed:.4f} s)")
            return connections
        
        same_stops = [s for s in await self.get_all_stations() if s.code == station_code]
        connections = [FgcLine.create_fgc_connection(s.line_id, s.line_code, s.line_name, s.line_description, s.line_color) for s in same_stops]
        await self.cache_service.set(f"fgc_station_connections_{station_code}", connections, ttl=3600*24)

        elapsed = (time.perf_counter() - start)
        logger.info(f"[{self.__class__.__name__}] get_fgc_station_connections({station_code}) from cache -> {len(connections)} connections (tiempo: {elapsed:.4f} s)")
        return connections
