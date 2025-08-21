from datetime import datetime
import aiohttp
import time

from typing import Any, Dict, List

from domain.tram.tram_line import TramLine
from domain.tram.tram_network import TramNetwork
from domain.tram.tram_stop import TramStop
from domain.tram.tram_connection import TramConnection, TramStopConnection
from domain.tram.next_tram import TramLineRoute, NextTram

#https://opendata.tram.cat/manual_en.pdf


class TramApiService:

    def __init__(self, client_id: str, client_secret: str):
        self.BASE_URL = "https://opendata.tram.cat"
        self.API_VERSION = "/api/v1"
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.ACCESS_TOKEN = None
        self.TOKEN_EXPIRES_AT = 0

    async def _fetch_access_token(self):
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
                else:
                    text = await response.text()
                    raise Exception(f"Error {response.status}: {text}")

    async def _get_valid_token(self) -> str:
        if not self.ACCESS_TOKEN or time.time() >= self.TOKEN_EXPIRES_AT:
            await self._fetch_access_token()
        return self.ACCESS_TOKEN

    async def _request(self, method: str, endpoint: str, use_base_url: bool = True, **kwargs) -> Any:
        """Método común para todas las llamadas HTTP."""
        token = await self._get_valid_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/json"

        endpoint = f"{self.BASE_URL}{self.API_VERSION}{endpoint}" if use_base_url else endpoint

        async with aiohttp.ClientSession() as session:
            async with session.request(method, endpoint, headers=headers, **kwargs) as response:
                if response.status == 401:
                    await self._fetch_access_token()
                    headers["Authorization"] = f"Bearer {self.ACCESS_TOKEN}"
                    async with session.request(method, endpoint, headers=headers, **kwargs) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()
                response.raise_for_status()
                return await response.json()


    async def get_networks(self, name: str = "", page: int = 1, page_size: int = 10, sort: str = ""):
        params = {"name": name, "page": page, "pageSize": page_size, "sort": sort}
        return await self._request("GET", "/networks", params=params)

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
        """
        Obtains information for a specific line by its ID.
        """
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
    ) -> List[TramStop]:
        """
        Obtains stops associated with a specific line by line ID.
        """
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
        # Remove None values to avoid sending them in the query
        params = {k: v for k, v in params.items() if v is not None}

        stops = await self._request("GET", f"/lines/{line_id}/stops", params=params)

        tram_line_stops: List[TramStop] = [
            TramStop(**stop)
            for stop in stops
        ]

        return tram_line_stops
    
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
        """
        Obtains connections associated with a specific stop by stop ID.
        """
        params = {
            "name": name,
            "image": image,
            "latitude": latitude,
            "longitude": longitude,
            "page": page,
            "pageSize": page_size,
            "sort": sort
        }
        # Remove None values to avoid sending them in the query
        params = {k: v for k, v in params.items() if v is not None}

        connections = await self._request("GET", f"/stops/{stop_id}/connections", params=params)

        tram_connections: List[TramConnection] = [ 
            TramConnection(
                id=connection['id'],
                name=connection['name'],
                latitude=connection['latitude'],
                longitude=connection['longitude'],
                order=connection['order'],
                image=connection['image'],
                stopConnections=[TramStopConnection(**sc) for sc in connection['stopConnections']]
            )
            for connection in connections 
        ]

        return tram_connections
    
    async def get_next_trams_at_stop(self, outbound_code: int, return_code: int):
        """
        Get the arrival times and destinations of the next scheduled TRAMs at a stop.

        :param code: The stop code (each stop has two codes depending on travel direction).
        :return: JSON with arrival times and destinations.
        """
        next_trams = await self._request("GET", f"https://tram-web-service.tram.cat/api/opendata/stopTimes?outboundCode={outbound_code}&returnCode={return_code}", use_base_url=False)
        
        routes_dict = {}
        for item in next_trams:
            key = (item["lineName"], item["code"], item["stopName"], item["destination"])

            next_tram = NextTram(
                vehicle_id=item["vehicleId"],
                occupancy=item["occupancy"],
                arrival_time=datetime.fromisoformat(item["arrivalTime"])
            )

            if key not in routes_dict:
                routes_dict[key] = TramLineRoute(
                    line_name=item["lineName"],
                    code=item["code"],
                    stop_name=item["stopName"],
                    destination=item["destination"],
                    next_trams=[next_tram]
                )
            else:
                routes_dict[key].next_trams.append(next_tram)

        return list(routes_dict.values())