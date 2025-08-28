from typing import List
import aiohttp
import re
import inspect

from domain.metro import MetroLine, MetroLineRoute, NextMetro, MetroConnection, MetroStation, create_metro_station, create_metro_access
from domain.bus import BusStop, BusLine, create_bus_stop, BusLineRoute, NextBus

from domain.transport_type import TransportType
from providers.helpers import logger


class TmbApiService:
    """Servicio para interactuar con la API de transporte (Metro y Bus)."""

    def __init__(self, app_key: str = None, app_id: str = None):
        self.logger = logger.getChild(self.__class__.__name__)
        self.BASE_URL_TRANSIT = 'https://api.tmb.cat/v1/transit'
        self.BASE_URL_ITRANSIT = "https://api.tmb.cat/v1/itransit"
        self.app_key = app_key
        self.app_id = app_id

    def _natural_key(self, line):
        name = line.ORIGINAL_NOM_LINIA.strip().upper()

        # Si es puramente numérica: agrupar todas con prefijo "" y ordenar por número
        if name.isdigit():
            return ("", int(name))

        # Si es alfanumérica tipo H1, X23, etc.
        match = re.match(r'^([A-Z]+)(\d+)$', name)
        if match:
            prefix, number = match.groups()
            return (prefix, int(number))

        # Si no encaja en ninguna, lo ponemos al final
        return (name, float('inf'))

    async def _get(self, endpoint: str, params: dict = None):
        """Realiza una petición GET a la API con app_id y app_key obligatorios."""

        merged_params = {
            "app_id": self.app_id,
            "app_key": self.app_key
        }
        if params:
            merged_params.update(params)

        current_method = inspect.currentframe().f_code.co_name
        self.logger.info(f"[{current_method}] GET → {endpoint}")

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=merged_params) as resp:
                resp.raise_for_status()
                return await resp.json()
            
    async def fetch_transit_items(self, url: str, model_class, *, filter_fn=None, sort_key=None, factory_fn=None):
        data = await self._get(url)
        features = data['features']

        items = []
        for feature in features:
            props = feature['properties']
            if filter_fn is None or filter_fn(props):
                if factory_fn:
                    item = factory_fn(feature)
                else:
                    item = model_class(**props)
                items.append(item)

        if sort_key:
            items.sort(key=sort_key)
        return items, data
    
    async def get_bus_lines(self) -> List[BusLine]:
        url = f'{self.BASE_URL_TRANSIT}/linies/bus'
        items, _ = await self.fetch_transit_items(url, BusLine, sort_key=self._natural_key)
        return items

    async def get_bus_line_stops(self, line_code) -> List[BusStop]:
        url = f'{self.BASE_URL_TRANSIT}/linies/bus/{line_code}/parades'

        from_origin, _ = await self.fetch_transit_items(
            url,
            BusStop,
            filter_fn=lambda props: props['ID_SENTIT'] == 1,
            sort_key=lambda x: x.ORDRE,
            factory_fn=create_bus_stop
        )

        from_destination, _ = await self.fetch_transit_items(
            url,
            BusStop,
            filter_fn=lambda props: props['ID_SENTIT'] == 2,
            sort_key=lambda x: x.ORDRE,
            factory_fn=create_bus_stop
        )

        return from_origin + from_destination

    async def get_metro_lines(self) -> List[MetroLine]:
        url = f'{self.BASE_URL_TRANSIT}/linies/metro'
        items, _ = await self.fetch_transit_items(url, MetroLine, sort_key=lambda x: x.NOM_LINIA)
        return items
    
    async def get_metro_stations(self) -> List[MetroStation]:
        url = f'{self.BASE_URL_TRANSIT}/estacions'
        data = await self._get(url)
        
        features = data['features']

        stations = []
        for feature in features:
            stations.append(create_metro_station(feature))

        stations.sort(key=lambda x: x.ORDRE_ESTACIO)
        return stations
    
    async def get_bus_stops(self) -> List[BusStop]:
        url = f'{self.BASE_URL_TRANSIT}/parades'
        data = await self._get(url)
        features = data['features']

        stations = []
        for feature in features:
            stations.append(create_bus_stop(feature))

        stations.sort(key=lambda x: x.ORDRE_LINIA)
        return stations

    async def get_stations_by_metro_line(self, line) -> List[MetroStation]:
        url = f'{self.BASE_URL_TRANSIT}/linies/metro/{line}/estacions'
        data = await self._get(url)
        features = data['features']

        stations = []
        for feature in features:
            stations.append(create_metro_station(feature))

        stations.sort(key=lambda x: x.ORDRE_ESTACIO)
        return stations

    # WIP
    async def get_next_scheduled_metro_at_station(self, station_id):
        url = f'{self.BASE_URL_ITRANSIT}/metro/estacions?estacions={station_id}&temps_teoric=true'
        data = await self._get(url)

        scheduled_routes = []
        for line in data.get("linies", []):
            for station in line.get("estacions", []):
                for route_data in station.get("linies_trajectes", []):
                    next_scheduled_metros = [
                    # NextMetro(**metro) for metro in route_data.get("propers_trens", [])
                    ]

    async def get_next_metro_at_station(self, station_id) -> List[MetroLineRoute]:
        url = f'{self.BASE_URL_ITRANSIT}/metro/estacions?estacions={station_id}'
        data = await self._get(url)

        routes = []
        for line in data.get("linies", []):
            for station in line.get("estacions", []):
                for route_data in station.get("linies_trajectes", []):
                    next_metros = [
                        NextMetro(**metro) for metro in route_data.get("propers_trens", [])
                    ]
                    route = MetroLineRoute(
                        codi_linia=route_data["codi_linia"],
                        nom_linia=route_data["nom_linia"],
                        color_linia=route_data["color_linia"],
                        codi_trajecte=route_data["codi_trajecte"],
                        desti_trajecte=route_data["desti_trajecte"],
                        propers_trens=next_metros
                    )
                    routes.append(route)
        return routes

    async def get_next_bus_at_stop(self, station_id) -> List[BusLineRoute]:
        url = f"{self.BASE_URL_ITRANSIT}/bus/parades/{station_id}"
        data = await self._get(url)

        routes = []
        for stop in data.get("parades", []):
            for route_data in stop.get("linies_trajectes", []):
                next_buses = [
                    NextBus(**bus) for bus in route_data.get("propers_busos", [])
                ]
                route = BusLineRoute(
                    id_operador=route_data["id_operador"],
                    transit_namespace=route_data["transit_namespace"],
                    codi_linia=route_data["codi_linia"],
                    nom_linia=route_data["nom_linia"],
                    codi_trajecte=route_data["codi_trajecte"],
                    desti_trajecte=route_data["desti_trajecte"],
                    id_sentit=route_data["id_sentit"],
                    propers_busos=next_buses
                )
                routes.append(route)
        return routes

    async def get_metro_station_accesses(self, group_station_code):
        url = f"https://api.tmb.cat/v1/transit/estacions/{group_station_code}/accessos"
        data = await self._get(url)
        features = data['features']

        accesses = []
        for feature in features:
            access = create_metro_access(feature)
            accesses.append(access)

        return accesses

    async def get_station_connections(self, metro_station_id):
        url = f"https://api.tmb.cat/v1/transit/linies/metro/estacions/{metro_station_id}/corresp"
        data = await self._get(url)
        features = data['features']

        connections = []
        for feature in features:
            props = feature["properties"]
            if props['NOM_OPERADOR'] == "Metro":
                connection = MetroConnection(**props)
                connections.append(connection) 

        return connections
    
    async def get_global_alerts(self, transport_type: TransportType):
        url = f"https://api.tmb.cat/v1/alerts/{transport_type.value}/channels/WEB"
        data = await self._get(url)
        return data['data']['alerts']
    
    async def get_line_alerts(self, transport_type: TransportType, line_name):
        url = f"https://api.tmb.cat/v1/alerts/{transport_type.value}/channels/WEB/routes/{line_name}"
        data = await self._get(url)
        return data['data']['alerts']