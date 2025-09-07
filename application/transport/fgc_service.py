import json
from typing import List

from application.cache_service import CacheService
from domain.fgc import FgcLine, FgcLineRoute, FgcStation, NextFgc
from domain.transport_type import TransportType
from providers.api import FgcApiService
from providers.helpers import logger
from providers.manager import LanguageManager
from providers.manager.user_data_manager import UserDataManager

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
        user_data_manager: UserDataManager = None,
    ):
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
            cache_ttl=3600 * 24,
        )

    async def get_all_stations(self) -> List[FgcStation]:
        # TODO: Complete integration
        fgc_stations_key = "fgc_stations"
        moute_stations_key = "moute_stations"

        cached_stations = await self._get_from_cache_or_data(
            fgc_stations_key, None, cache_ttl=3600 * 24
        )
        # moute_stations = await self._get_from_cache_or_data(moute_stations_key, None, cache_ttl=3600*24)

        if cached_stations is not None:
            return cached_stations

        # if moute_stations is None:
        #    moute_stations = await self.fgc_api_service.get_all_stations()
        #    await self._get_from_cache_or_data(moute_stations_key, moute_stations, cache_ttl=3600*24)

        lines = await self.get_all_lines()
        stations = []
        for line in lines:
            line_stations = await self.fgc_api_service.get_stations_by_line(line.id)

            for line_station in line_stations:
                moute_station = await self.fgc_api_service.get_near_stations(
                    line_station.lat, line_station.lon
                )
                # moute_station = next((s for s in moute_stations if str(TransportType.FGC.id) in s.get('tipusTransports') and line_station.name in s.get('desc')), None)
                if any(moute_station):
                    line_station.moute_id = moute_station[0].get("id")

            stations += line_stations

        logger.warning(
            f"The following FGC stations where not found:\n {[s for s in stations if s.moute_id is None]}"
        )
        return await self._get_from_cache_or_data(
            fgc_stations_key, stations, cache_ttl=3600 * 24
        )

    async def get_stations_by_line(self, line_id) -> List[FgcStation]:
        stations = await self.get_all_stations()
        return [s for s in stations if s.line_id == line_id]

    async def get_station_routes(self, station_name, moute_id, line_name):
        routes = await self._get_from_cache_or_data(
            f"fgc_station_{station_name}_routes", None, cache_ttl=30
        )

        if routes is None:
            if moute_id != None:
                raw_routes = await self.fgc_api_service.get_moute_next_departures(
                    moute_id, line_name
                )

                routes = []
                for direction, trips in raw_routes.items():
                    nextFgc = []
                    for trip in trips:
                        nextFgc.append(
                            NextFgc(
                                codi_servei="",
                                temps_arribada=trip.get("departure_time"),
                            )
                        )
                    routes.append(
                        FgcLineRoute(
                            desti_trajecte=direction,
                            propers_trens=nextFgc,
                            nom_linia=line_name,
                            codi_linia=line_name,
                            color_linia=None,
                            codi_trajecte=None,
                        )
                    )
            else:
                raw_routes = await self.fgc_api_service.get_next_departures(
                    station_name, line_name
                )

                routes = []
                for direction, trips in raw_routes.items():
                    nextFgc = []
                    for trip in trips:
                        nextFgc.append(
                            NextFgc(
                                codi_servei=trip.get("trip_id"),
                                temps_arribada=trip.get("departure_time"),
                            )
                        )
                    routes.append(
                        FgcLineRoute(
                            desti_trajecte=direction,
                            propers_trens=nextFgc,
                            nom_linia=line_name,
                            codi_linia=line_name,
                            color_linia=None,
                            codi_trajecte=None,
                        )
                    )

            routes = await self._get_from_cache_or_data(
                f"fgc_station_{station_name}_routes", routes, cache_ttl=30
            )

        return "\n\n".join(str(route) for route in routes)

    async def get_station_by_id(self, station_id, line_id) -> FgcStation:
        """
        Retrieve a station by its code.
        """
        stations = await self.get_stations_by_line(line_id)
        station = next((s for s in stations if str(s.id) == str(station_id)), None)
        logger.debug(
            f"[{self.__class__.__name__}] get_station_by_id({station_id}, line {line_id}) -> {station}"
        )
        return station

    async def get_line_by_id(self, line_id) -> FgcLine:
        """
        Retrieve a station by its code.
        """
        lines = await self.get_all_lines()
        line = next((l for l in lines if str(l.id) == str(line_id)), None)
        logger.debug(f"[{self.__class__.__name__}] get_line_by_id({line_id}) -> {line}")
        return line
