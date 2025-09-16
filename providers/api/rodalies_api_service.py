import aiohttp
import inspect
from datetime import datetime
from typing import Any, List

from domain.transport_type import TransportType
from providers.helpers import logger
from domain.rodalies import RodaliesLine, RodaliesStation
from domain import NextTrip, LineRoute, normalize_to_seconds


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
        self.logger.debug(f"[{current_method}] {method.upper()} → {url} | Params: {kwargs.get('params', {})}")

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
                stations.extend(
                    RodaliesStation.create_rodalies_station(station_data)
                    for station_data in line_data["stations"]
                )
                lines.append(RodaliesLine.create_rodalies_line(line_data, stations))

        return lines

    async def get_line_by_id(self, line_id: int) -> RodaliesLine:
        """Fetch a single Rodalies line by ID."""
        line_data = await self._request("GET", f"/lines/{line_id}")
        stations = []
        stations.extend(
            RodaliesStation.create_rodalies_station(station_data)
            for station_data in line_data["stations"]
        )
        return RodaliesLine.create_rodalies_line(line_data, stations)

    async def get_global_alerts(self):
        alerts = await self._request("GET", "/notices?limit=500&sort=date,desc&sort=time,desc")
        return alerts['included']

    # ==== Stations ====
    async def get_next_trains_at_station(self, station_id: int, line_id: str) -> List[RodaliesStation]:
        """Fetch all stations for a given line."""
        next_rodalies = await self._request("GET", f"/departures?stationId={station_id}&minute=90&fullResponse=true&lang=ca")       
        
        routes_dict = {}
        for item in next_rodalies["trains"]:
            line = item["line"]
            if str(line["id"]) == str(line_id):
                key = (line["name"], line["id"], item["destinationStation"]["name"])

                next_rodalies = NextTrip(
                        id=item["technicalNumber"],
                        arrival_time=normalize_to_seconds(datetime.fromisoformat(item["departureDateHourSelectedStation"]).timestamp()),
                        platform=item["platformSelectedStation"],
                        delay_in_minutes=item["delay"]
                    )
                
                if key not in routes_dict:
                    routes_dict[key] = LineRoute(
                        route_id=line_id,
                        line_name=line_id,
                        line_id=line_id,
                        destination=item["destinationStation"]["name"],
                        next_trips=[next_rodalies],
                        color=None,
                        line_type=TransportType.RODALIES
                    )
                else:
                    routes_dict[key].next_trips.append(next_rodalies)

        return list(routes_dict.values())
        