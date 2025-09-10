import time
import aiohttp
import inspect
from datetime import datetime
from typing import Any, Dict, List

from domain.tram import TramLine, TramNetwork, TramStation, TramConnection, TramStationConnection, create_tram_station
from domain import NextTrip, LineRoute, normalize_to_seconds

from domain.transport_type import TransportType
from providers.helpers import logger


class TramApiService:
    """Servicio para interactuar con la API de TRAM."""

    def __init__(self, client_id: str, client_secret: str):
        self.logger = logger.getChild(self.__class__.__name__)
        self.BASE_URL = "https://opendata.tram.cat"
        self.API_VERSION = "/api/v1"
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.ACCESS_TOKEN = None
        self.TOKEN_EXPIRES_AT = 0

    async def _fetch_access_token(self):
        current_method = inspect.currentframe().f_code.co_name
        self.logger.info(f"[{current_method}] Fetching new access token")

        url = f"{self.BASE_URL}/connect/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.ACCESS_TOKEN = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self.TOKEN_EXPIRES_AT = time.time() + expires_in - 60
                    self.logger.info(f"[{current_method}] Access token successfully retrieved")
                else:
                    text = await response.text()
                    self.logger.error(f"[{current_method}] Failed to fetch token: {response.status} - {text}")
                    raise Exception(f"Error {response.status}: {text}")

    async def _get_valid_token(self) -> str:
        current_method = inspect.currentframe().f_code.co_name
        if not self.ACCESS_TOKEN or time.time() >= self.TOKEN_EXPIRES_AT:
            self.logger.info(f"[{current_method}] Token expired or missing → fetching new one")
            await self._fetch_access_token()
        return self.ACCESS_TOKEN

    async def _request(self, method: str, endpoint: str, use_base_url: bool = True, **kwargs) -> Any:
        """Método común para todas las llamadas HTTP."""
        current_method = inspect.currentframe().f_code.co_name
        token = await self._get_valid_token()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/json"

        endpoint = f"{self.BASE_URL}{self.API_VERSION}{endpoint}" if use_base_url else endpoint

        self.logger.info(f"[{current_method}] {method.upper()} → {endpoint} | Params: {kwargs.get('params', {})}")

        async with aiohttp.ClientSession() as session:
            async with session.request(method, endpoint, headers=headers, **kwargs) as response:
                if response.status == 401:
                    self.logger.warning(f"[{current_method}] Token expired → retrying with new token")
                    await self._fetch_access_token()
                    headers["Authorization"] = f"Bearer {self.ACCESS_TOKEN}"
                    async with session.request(method, endpoint, headers=headers, **kwargs) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()

                response.raise_for_status()
                return await response.json()

    async def get_networks(self, name: str = "", page: int = 1, page_size: int = 10, sort: str = ""):
        return await self._request("GET", "/networks", params={
            "name": name,
            "page": page,
            "pageSize": page_size,
            "sort": sort
        })

    async def get_lines(
        self,
        name: str = "",
        description: str = "",
        network: str = "",
        image: str = "",
        code: int = None,
        page: int = 1,
        page_size: int = 100,
        sort: str = ""
    ) -> List[TramLine]:
        params: Dict[str, Any] = {
            "name": name,
            "description": description,
            "network": network,
            "image": image,
            "page": page,
            "pageSize": page_size,
            "sort": sort
        }
        if code is not None:
            params["code"] = code

        lines = await self._request("GET", "/lines", params=params)

        tram_lines: List[TramLine] = [
            TramLine(
                name=line["name"],
                description=line["description"],
                network=TramNetwork(**line["network"]),
                code=line["code"],
                image=line["image"],
                id=line["id"]
            )
            for line in lines
        ]

        return tram_lines

    async def get_line_by_id(self, line_id: int) -> TramLine:
        return await self._request("GET", f"/lines/{line_id}")

    async def get_stops_on_line(
        self,
        line_id: int,
        name: str = "",
        description: str = "",
        gtfsCode: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
        outboundCode: int | None = None,
        returnCode: int | None = None,
        image: str = "",
        page: int = 1,
        page_size: int = 100,
        sort: str = ""
    ) -> List[TramStation]:
        params = {
            "name": name,
            "description": description,
            "gtfsCode": gtfsCode,
            "latitude": latitude,
            "longitude": longitude,
            "outboundCode": outboundCode,
            "returnCode": returnCode,
            "image": image,
            "page": page,
            "pageSize": page_size,
            "sort": sort
        }
        params = {k: v for k, v in params.items() if v is not None}

        api_stops = await self._request("GET", f"/lines/{line_id}/stops", params=params)

        stops = []
        stops.extend(create_tram_station(stop) for stop in api_stops)
        return stops

    async def get_stops(
        self,
        name: str = "",
        description: str = "",
        gtfsCode: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
        outboundCode: int | None = None,
        returnCode: int | None = None,
        image: str = "",
        page: int = 1,
        page_size: int = 100,
        sort: str = ""
    ) -> List[TramStation]:
        params = {
            "name": name,
            "description": description,
            "gtfsCode": gtfsCode,
            "latitude": latitude,
            "longitude": longitude,
            "outboundCode": outboundCode,
            "returnCode": returnCode,
            "image": image,
            "page": page,
            "pageSize": page_size,
            "sort": sort
        }
        params = {k: v for k, v in params.items() if v is not None}
        api_stops = await self._request("GET", "/stops", params=params)
        stops = []
        stops.extend(create_tram_station(stop) for stop in api_stops)
        return stops

    async def get_connections_at_stop(
        self,
        stop_id: int,
        name: str = "",
        image: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
        page: int = 1,
        page_size: int = 100,
        sort: str = ""
    ) -> List[TramConnection]:
        params = {
            "name": name,
            "image": image,
            "latitude": latitude,
            "longitude": longitude,
            "page": page,
            "pageSize": page_size,
            "sort": sort
        }
        params = {k: v for k, v in params.items() if v is not None}

        connections = await self._request("GET", f"/stops/{stop_id}/connections", params=params)

        return [
            TramConnection(
                id=connection['id'],
                name=connection['name'],
                latitude=connection['latitude'],
                longitude=connection['longitude'],
                order=connection['order'],
                image=connection['image'],
                stopConnections=[TramStationConnection(**sc) for sc in connection['stopConnections']]
            )
            for connection in connections
        ]

    async def get_next_trams_at_stop(self, outbound_code: int, return_code: int):
        next_trams = await self._request(
            "GET",
            f"https://tram-web-service.tram.cat/api/opendata/stopTimes"
            f"?outboundCode={outbound_code}&returnCode={return_code}",
            use_base_url=False
        )

        routes_dict = {}
        for item in next_trams:
            key = (item["lineName"], item["code"], item["stopName"], item["destination"])

            next_tram = NextTrip(
                id=item["vehicleId"],
                arrival_time=normalize_to_seconds(int(datetime.fromisoformat(item["arrivalTime"]).timestamp()))
            )

            if key not in routes_dict:
                routes_dict[key] = LineRoute(
                    line_id=item["lineName"],
                    route_id=item["code"],
                    line_name=item["lineName"],
                    destination=item["destination"],
                    next_trips=[next_tram],
                    line_type=TransportType.TRAM,
                    color="008E78"
                )
            else:
                routes_dict[key].next_trips.append(next_tram)

        return list(routes_dict.values())
