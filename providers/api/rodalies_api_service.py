import time
import aiohttp
import inspect
from datetime import datetime
from typing import Any, Dict, List

from providers.helpers import logger
from domain.rodalies import RodaliesLine, RodaliesStation, create_rodalies_line, create_rodalies_station


class RodaliesApiService:
    """Service to interact with Rodalies de Catalunya API."""

    BASE_URL = "https://serveisgrs.rodalies.gencat.cat/api"

    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)

    async def _request(self, method: str, endpoint: str, use_base_url: bool = True, **kwargs) -> Any:
        """Generic HTTP request handler with token authentication."""
        current_method = inspect.currentframe().f_code.co_name
        headers = kwargs.pop("headers", {})
        headers["Accept"] = "application/json"

        url = f"{self.BASE_URL}{endpoint}" if use_base_url else endpoint
        self.logger.info(f"[{current_method}] {method.upper()} → {url} | Params: {kwargs.get('params', {})}")

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, **kwargs) as resp:
                if resp.status == 401:
                    self.logger.warning(f"[{current_method}] Token expired → retrying")
                    async with session.request(method, url, headers=headers, **kwargs) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json()

                resp.raise_for_status()
                return await resp.json()

    # ==== Lines ====
    async def get_lines(self, type: str = "RODALIES"):
        """Fetch all Rodalies lines."""

        lines = []
        for type in ["RODALIES", "REGIONAL"]:
            data = await self._request("GET", f"/lines?type={type}&page=0&limit=100&lang=ca", params=None)
            
            for line_data in data["included"]:
                stations = []
                for station_data in line_data["stations"]:
                    stations.append(create_rodalies_station(station_data))
                lines.append(create_rodalies_line(line_data, stations))
            
        return lines

    async def get_line_by_id(self, line_id: int) -> RodaliesLine:
        """Fetch a single Rodalies line by ID."""
        line_data = await self._request("GET", f"/lines/{line_id}")
        stations = []
        for station_data in line_data["stations"]:
            stations.append(create_rodalies_station(station_data))
        return create_rodalies_line(line_data, stations)

    # ==== Stations ====
    async def get_stations_on_line(self, line_id: int) -> List[RodaliesStation]:
        """Fetch all stations for a given line."""
        data = await self._request("GET", f"/linies/{line_id}/estacions")
        return [create_rodalies_station(station) for station in data.get("features", [])]
'''
    async def get_station_by_id(self, station_id: int) -> RodaliesStation:
        """Fetch detailed info for a specific station."""
        data = await self._request("GET", f"/estacions/{station_id}")
        return create_rodalies_station(data)

    # ==== Next trains ====
    async def get_next_trains_at_station(self, line_id: int, station_id: int) -> List[RodaliesLineRoute]:
        """Get next trains for a line at a specific station."""
        data = await self._request("GET", f"/linies/{line_id}/estacions/{station_id}/horaris")
        routes = []
        for route_data in data.get("linies_trajectes", []):
            next_trains = [NextTrain(**t) for t in route_data.get("propers_trens", [])]
            routes.append(RodaliesLineRoute(
                codi_linia=route_data["codi_linia"],
                nom_linia=route_data["nom_linia"],
                color_linia=route_data.get("color_linia", ""),
                codi_trajecte=route_data.get("codi_trajecte", ""),
                desti_trajecte=route_data.get("desti_trajecte", ""),
                propers_trens=next_trains
            ))
        return routes

    # ==== Alerts ====
    async def get_alerts(self) -> Dict[str, Any]:
        """Fetch current service alerts."""
        return await self._request("GET", "/alerts")

    '''


api = RodaliesApiService()
api.get_lines()