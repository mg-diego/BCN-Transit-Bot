from datetime import datetime
from io import StringIO
import aiohttp
import inspect
import asyncio
from typing import Any, Dict, List

import pandas as pd

from domain.fgc import FgcLine, FgcStation, create_fgc_line
from providers.helpers import logger
from google.transit import gtfs_realtime_pb2


class FgcApiService:
    """Service to interact with FGC API."""

    BASE_URL = "https://dadesobertes.fgc.cat/api/explore/v2.1/catalog/datasets"
    GTFS_RT_URL = "https://dadesobertes.fgc.cat/api/explore/v2.1/catalog/datasets/trip-updates-gtfs_realtime/files/735985017f62fd33b2fe46e31ce53829"


    def __init__(self):
        # Almacenaremos los CSV descargados
        self._routes = None
        self._stops = None
        self._trips = None
        self._stop_times = None
        self.logger = logger.getChild(self.__class__.__name__)

    async def _request(
        self,
        method: str,
        endpoint: str,
        use_base_url: bool = True,
        raw: bool = False,
        text: bool = False,
        **kwargs
    ) -> Any:
        """Generic HTTP request handler supporting JSON, text and raw bytes."""
        current_method = inspect.currentframe().f_code.co_name
        headers = kwargs.pop("headers", {})
        headers["Accept"] = "*/*" if raw or text else "application/json"

        url = f"{self.BASE_URL}{endpoint}" if use_base_url else endpoint
        self.logger.info(f"[{current_method}] {method.upper()} → {url} | Params: {kwargs.get('params', {})}")

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, **kwargs) as resp:
                if resp.status == 401:
                    async with session.request(method, url, headers=headers, **kwargs) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.read() if raw else (await retry_resp.text() if text else await retry_resp.json())

                resp.raise_for_status()
                if raw:
                    return await resp.read()
                elif text:
                    return await resp.text()
                else:
                    return await resp.json()
    
    # ----------------------------
    # Métodos para obtener estaciones
    # ----------------------------
    async def _get_file_urls(self) -> dict:
        """Obtener dinámicamente las URLs de los ficheros GTFS necesarios"""
        data = await self._request("GET", '/gtfs_zip/records?limit=100')
        urls = {}
        for record in data.get("results", []):
            file_info = record.get("file", {})
            filename = file_info.get("filename")
            url = file_info.get("url")
            if filename and url and filename in ["routes.txt", "stops.txt", "trips.txt", "stop_times.txt"]:
                key = filename.replace(".txt", "")
                urls[key] = url
        return urls

    async def _load_csvs(self):
        """Descargar los CSVs una sola vez y guardarlos en la clase"""
        if self._routes is not None:
            return

        urls = await self._get_file_urls()
        self._routes = pd.read_csv(StringIO(await self._request("GET", urls["routes"], use_base_url=False, text=True)))
        self._stops = pd.read_csv(StringIO(await self._request("GET", urls["stops"], use_base_url=False, text=True)))
        self._trips = pd.read_csv(StringIO(await self._request("GET", urls["trips"], use_base_url=False, text=True)))
        self._stop_times = pd.read_csv(StringIO(await self._request("GET", urls["stop_times"], use_base_url=False, text=True)))

    async def get_stations_by_line(self, line_name: str) -> List[FgcStation]:
        """Obtener todas las estaciones de una línea concreta con orden correcto"""
        await self._load_csvs()

        # 1. Filtrar por línea
        route = self._routes[self._routes["route_short_name"] == line_name]
        if route.empty:
            raise ValueError(f"No se encontró la línea {line_name}")
        route_id = route.iloc[0]["route_id"]

        trips_for_route = self._trips[self._trips["route_id"] == route_id]
        if trips_for_route.empty:
            return []

        # 2. Tomamos el primer trip como referencia para el orden
        first_trip_id = trips_for_route.iloc[0]["trip_id"]

        stop_times_line = self._stop_times[self._stop_times["trip_id"] == first_trip_id]
        stop_times_line = stop_times_line.sort_values("stop_sequence")

        # 3. Asignar orden incremental limpio
        stop_order_map = {stop_id: idx + 1 for idx, stop_id in enumerate(stop_times_line["stop_id"].tolist())}

        # 4. Obtener info de estaciones
        stations_df = self._stops[self._stops["stop_id"].isin(stop_order_map.keys())].copy()

        # 5. Crear lista de FgcStation con order correcto
        stations = [
            FgcStation(
                id=row["stop_id"],
                name=row["stop_name"],
                lat=float(row["stop_lat"]),
                lon=float(row["stop_lon"]),
                order=stop_order_map[row["stop_id"]],
                line_id=line_name
            )
            for _, row in stations_df.iterrows()
        ]

        # 6. Ordenar la lista por 'order'
        stations.sort(key=lambda x: x.order)
        return stations
    
    async def get_realtime_departures(self, station_name: str, line_name: str, limit: int = 5) -> List[Dict]:
        """
        Obtiene las próximas salidas en tiempo real para una estación y línea concreta.
        """
        # 1. Aseguramos que los CSVs están cargados
        await self._load_csvs()

        # 2. Obtener stop_id por nombre de estación
        stop = self._stops[self._stops["stop_name"].str.lower() == station_name.lower()]
        if stop.empty:
            raise ValueError(f"No se encontró la estación {station_name}")
        stop_id = stop.iloc[0]["stop_id"]

        # 3. Obtener route_id por nombre de línea
        route = self._routes[self._routes["route_short_name"] == line_name]
        if route.empty:
            raise ValueError(f"No se encontró la línea {line_name}")
        route_id = route.iloc[0]["route_id"]

        # 4. Descargar el feed GTFS-RT usando _request()
        data = await self._request("GET", self.GTFS_RT_URL, use_base_url=False, raw=True)

        # 5. Parsear el feed GTFS-RT
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(data)

        # 6. Filtrar próximas salidas de la línea y estación
        departures = []
        for entity in feed.entity:
            if not entity.HasField("trip_update"):
                continue

            trip_update = entity.trip_update
            if trip_update.trip.route_id != route_id:
                continue

            for stu in trip_update.stop_time_update:
                if stu.stop_id == stop_id and (stu.HasField("departure") or stu.HasField("arrival")):
                    ts = stu.departure.time if stu.HasField("departure") else stu.arrival.time
                    departures.append({
                        "trip_id": trip_update.trip.trip_id,
                        "departure_time": datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                    })

        # 7. Ordenar y limitar resultados
        departures.sort(key=lambda x: x["departure_time"])
        return departures[:limit]