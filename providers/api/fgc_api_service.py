from datetime import datetime
from io import StringIO
import ssl
import time
from zoneinfo import ZoneInfo
import aiohttp
import inspect
import asyncio
from typing import Any, Dict, List

import pandas as pd

from domain.fgc import FgcLine, FgcStation
from domain.transport_type import TransportType
from providers.helpers import logger
from google.transit import gtfs_realtime_pb2


class FgcApiService:
    """Service to interact with FGC API."""

    FGC_BASE_URL = "https://dadesobertes.fgc.cat/api/explore/v2.1/catalog/datasets"
    MOUTE_BASE_URL = "https://mou-te.gencat.cat/MouteAPI/rest/infrastructure"
    GTFS_RT_URL = "https://dadesobertes.fgc.cat/api/explore/v2.1/catalog/datasets/trip-updates-gtfs_realtime/files/735985017f62fd33b2fe46e31ce53829"


    def __init__(self):        
        self._routes = None
        self._stops = None
        self._trips = None
        self._stop_times = None
        self.logger = logger.getChild(self.__class__.__name__)

    async def _request(
        self,
        method: str,
        endpoint: str,
        use_FGC_BASE_URL: bool = True,
        raw: bool = False,
        text: bool = False,
        **kwargs
    ) -> Any:
        """Generic HTTP request handler supporting JSON, text and raw bytes."""
        current_method = inspect.currentframe().f_code.co_name
        headers = kwargs.pop("headers", {})
        headers["Accept"] = "*/*" if raw or text else "application/json"

        url = f"{self.FGC_BASE_URL}{endpoint}" if use_FGC_BASE_URL else endpoint
        self.logger.debug(f"[{current_method}] {method.upper()} → {url} | Params: {kwargs.get('params', {})}")

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, ssl=ssl_context, **kwargs) as resp:
                if resp.status == 401:
                    async with session.request(method, url, headers=headers, ssl=ssl_context, **kwargs) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.read() if raw else (await retry_resp.text() if text else await retry_resp.json())

                resp.raise_for_status()
                if raw:
                    return await resp.read()
                elif text:
                    return await resp.text()
                else:
                    return await resp.json()
    
    async def get_all_lines(self) -> List[FgcLine]: 
        data = await self._request("GET", "/lineas-red-fgc/records?limit=100", params=None)
        lines = [FgcLine.create_fgc_line(l) for l in data['results'] if l['route_id'] != "L1"] # Excluir Cremallera de Nuria
        lines.sort(key= lambda x: x.id)
        return lines
    
    async def get_near_stations(self, lat, lon, radius = 250):
        data = await self._request("GET", f"{self.MOUTE_BASE_URL}/nearbyotp?radius={radius}&coordX={lon}&coordY={lat}&language=ca_ES", params=None, use_FGC_BASE_URL=False)
        return [s for s in data['transports'] if str(TransportType.FGC.id) in s.get("tipusTransports")]

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
        self._routes = pd.read_csv(StringIO(await self._request("GET", urls["routes"], use_FGC_BASE_URL=False, text=True)))
        self._stops = pd.read_csv(StringIO(await self._request("GET", urls["stops"], use_FGC_BASE_URL=False, text=True)))
        self._trips = pd.read_csv(StringIO(await self._request("GET", urls["trips"], use_FGC_BASE_URL=False, text=True)))
        self._stop_times = pd.read_csv(StringIO(await self._request("GET", urls["stop_times"], use_FGC_BASE_URL=False, text=True)))

    async def get_stations_by_line(self, line_name: str) -> List[FgcStation]:
        """Obtener todas las estaciones de una línea concreta con orden correcto"""
        await self._load_csvs()

        route = self._routes[self._routes["route_short_name"] == line_name]
        if route.empty:
            raise ValueError(f"No se encontró la línea {line_name}")
        route_id = route.iloc[0]["route_id"]

        trips_for_route = self._trips[self._trips["route_id"] == route_id]
        if trips_for_route.empty:
            return []

        first_trip_id = trips_for_route.iloc[0]["trip_id"]

        stop_times_line = self._stop_times[self._stop_times["trip_id"] == first_trip_id]
        stop_times_line = stop_times_line.sort_values("stop_sequence")

        stop_order_map = {stop_id: idx + 1 for idx, stop_id in enumerate(stop_times_line["stop_id"].tolist())}

        stations_df = self._stops[self._stops["stop_id"].isin(stop_order_map.keys())].copy()
        stations_df = stations_df.dropna(subset=["stop_id"])

        stations = [
            FgcStation.create_fgc_station(row, line_name=line_name, order=stop_order_map[row["stop_id"]])
            for _, row in stations_df.iterrows()
        ]

        # 6. Ordenar la lista por 'order'
        stations.sort(key=lambda x: x.order)
        return stations

    async def get_moute_next_departures(self, moute_id):
        data = await self._request("GET", f"{self.MOUTE_BASE_URL}/nextdeparturesNEW?paradaId={moute_id}&useRealTime=true&language=ca_ES", params=None, use_FGC_BASE_URL=False)
        
        lines = data.get("parada", {}).get("lineas", {}).get("linia", [])
        if isinstance(lines, dict): 
            lines = [lines]

        madrid_tz = ZoneInfo("Europe/Madrid")

        next_departures = {}
        
        for line in lines:
            line_id = line['idLinia']
            line_name = line.get('nomLinia')
            next_departures[line_name] = {}
            
            all_departures = data.get("sortides", {}).get("sortida", [])
            if not all_departures: continue
            
            directions = set([s["direccio"] for s in all_departures if line_id in s.get("tripId", "")])
            
            for direction in directions:
                next_departures[line_name][direction] = []
                
                sortides_realtime = [s for s in all_departures if line_id in s["tripId"] and s.get("realtime") and s["direccio"] == direction]
                sortides_scheduled = [s for s in all_departures if line_id in s["tripId"] and not s.get("realtime") and s["direccio"] == direction]

                for rt in sortides_realtime:
                    dt = datetime(
                        year=int(rt["any"]), 
                        month=int(rt["mes"]), 
                        day=int(rt["dia"]), 
                        hour=int(rt["hora"]), 
                        minute=int(rt["minuts"]),
                        tzinfo=madrid_tz
                    )
                    
                    next_departures[line_name][direction].append({
                        "departure_time": int(dt.timestamp()),
                        "type": "RT"
                    })

                for scheduled in sortides_scheduled:
                    if len(next_departures[line_name][direction]) < 3:
                        dt = datetime(
                            year=int(scheduled["any"]), 
                            month=int(scheduled["mes"]), 
                            day=int(scheduled["dia"]), 
                            hour=int(scheduled["hora"]), 
                            minute=int(scheduled["minuts"]),
                            tzinfo=madrid_tz
                        )

                        next_departures[line_name][direction].append({
                            "departure_time": int(dt.timestamp()),
                            "type": "Scheduled"
                        })
                    else:
                        break

        return next_departures
        

    async def get_next_departures(self, station_name: str, line_name: str, max_results: int = 5) -> Dict[str, List[Dict]]:
        log_file = "realtime_departures.log"

        madrid_tz = ZoneInfo("Europe/Madrid")

        def log(msg: str):
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now(tz=madrid_tz).strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

        # Resetear log
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("=== Nueva ejecución ===\n")

        # Cargar CSVs
        await self._load_csvs()

        # 1️⃣ Buscar estación
        stop = self._stops[self._stops["stop_name"].str.lower() == station_name.lower()]
        if stop.empty:
            log(f"No se encontró la estación {station_name}")
            return {}
        stop_id = stop.iloc[0]["stop_id"]
        log(f"STOP ({stop_id}):\n{stop}")

        # 2️⃣ Buscar línea
        route = self._routes[self._routes["route_short_name"] == line_name]
        if route.empty:
            log(f"No se encontró la línea {line_name}")
            return {}
        route_id = route.iloc[0]["route_id"]
        log(f"ROUTE ({route_id}):\n{route}")

        # 3️⃣ Obtener todos los trip_id de esta línea
        trip_ids = set(self._trips[self._trips["route_id"] == route_id]["trip_id"])
        log(f"TRIPS_IDS for '{route_id}':\n{trip_ids}")

        departures_by_direction = {}
        now_ts = time.time()
        seen_departures = set()  # (trip_instance_id, direction_id)

        # 4️⃣ Procesar feed RT
        try:
            data = await self._request("GET", self.GTFS_RT_URL, use_FGC_BASE_URL=False, raw=True)
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(data)
        except Exception as e:
            log(f"No se pudo descargar/parsear feed RT: {e}")
            feed = None

        rt_trip_ids = set()

        if feed:
            log(f"FEED: \n{feed.entity}")
            for entity in feed.entity:
                if not entity.HasField("trip_update"):
                    continue
                trip_update = entity.trip_update
                if trip_update.trip.trip_id not in trip_ids:
                    continue
                direction_id = getattr(trip_update.trip, "direction_id", 0)
                stop_time_updates = trip_update.stop_time_update
                if not stop_time_updates:
                    continue

                # Última parada para nombre de dirección
                last_stop_id = stop_time_updates[-1].stop_id
                last_stop_row = self._stops[self._stops["stop_id"] == last_stop_id]
                direction_name = f"dir_{direction_id}" if last_stop_row.empty else last_stop_row.iloc[0]["stop_name"]

                for stu in stop_time_updates:
                    if stu.stop_id != stop_id:
                        continue
                    if not stu.HasField("departure") or not stu.departure.HasField("time"):
                        continue
                    ts = stu.departure.time
                    if ts < now_ts:
                        continue

                    trip_instance_id = trip_update.trip.trip_id.split("|")[1]
                    key = (trip_instance_id, direction_name)
                    if key in seen_departures:
                        continue
                    seen_departures.add(key)

                    departures_by_direction.setdefault(direction_name, []).append({
                        "trip_id": trip_update.trip.trip_id,
                        "departure_time": ts,
                        "type": "RT"
                    })
                    rt_trip_ids.add(trip_update.trip.trip_id)
                    log(f"--> Coincidencia RT: trip_id={trip_update.trip.trip_id}, ts={ts}, direction={direction_name}")

                    if len(departures_by_direction[direction_name]) >= max_results:
                        break

        # 5️⃣ Procesar planificados (100% vectorizado y robusto)
        stop_times_for_stop = self._stop_times[
            (self._stop_times["stop_id"] == stop_id) &
            (self._stop_times["trip_id"].isin(trip_ids - rt_trip_ids))
        ].copy()

        # Si no hay datos, devolvemos lo que tengamos
        if stop_times_for_stop.empty:
            log(f"No hay salidas planificadas para {station_name}")
            return departures_by_direction

        # Vectorizamos el cálculo de departure_ts
        def to_timestamp(dep_time: str) -> float:
            try:
                h, m, s = map(int, dep_time.split(":"))
            except ValueError:
                return float("inf")  # Si hay datos corruptos, los descartamos
            extra_days = h // 24
            h %= 24
            ts = datetime.now(tz=madrid_tz).replace(hour=h, minute=m, second=s, microsecond=0).timestamp()
            return ts + extra_days * 24 * 3600

        stop_times_for_stop["departure_ts"] = stop_times_for_stop["departure_time"].map(to_timestamp)
        stop_times_for_stop = stop_times_for_stop[stop_times_for_stop["departure_ts"] >= now_ts]

        # Si no hay salidas futuras, devolvemos lo que tengamos
        if stop_times_for_stop.empty:
            return departures_by_direction

        # Si falta la columna direction_id, la creamos
        trips_df = self._trips.copy()
        if "direction_id" not in trips_df.columns:
            trips_df["direction_id"] = 0

        # Merge para añadir direction_id
        stop_times_for_stop = stop_times_for_stop.merge(
            trips_df[["trip_id", "direction_id"]],
            on="trip_id",
            how="left"
        )

        # Calcular última parada de cada trip, renombrando explícitamente la columna
        last_stops = (
            self._stop_times
            .sort_values("stop_sequence")
            .groupby("trip_id", as_index=False)
            .agg({"stop_id": "last"})
            .rename(columns={"stop_id": "last_stop_id"})
        )
        stop_times_for_stop = stop_times_for_stop.merge(last_stops, on="trip_id", how="left")

        # Merge con stops usando last_stop_id
        stop_times_for_stop = stop_times_for_stop.merge(
            self._stops[["stop_id", "stop_name"]],
            left_on="last_stop_id",
            right_on="stop_id",
            how="left"
        )

        # Crear trip_instance_id vectorizado
        stop_times_for_stop["trip_instance_id"] = stop_times_for_stop["trip_id"].str.split("|").str[1]

        # Crear direction_name con fallback
        stop_times_for_stop["direction_name"] = stop_times_for_stop.apply(
            lambda r: r["stop_name"] if pd.notna(r["stop_name"]) else f"dir_{r['direction_id']}",
            axis=1
        )

        # Eliminar duplicados usando trip_instance_id + direction_name
        stop_times_for_stop = stop_times_for_stop.drop_duplicates(subset=["trip_instance_id", "direction_name"])

        # Agrupar por dirección y coger los max_results primeros
        departures_by_direction_df = (
            stop_times_for_stop
            .sort_values("departure_ts")
            .groupby("direction_name")
            .head(max_results)
            [["direction_name", "trip_id", "departure_ts"]]
        )

        # Convertir DataFrame a diccionario final
        for direction_name, group in departures_by_direction_df.groupby("direction_name"):
            departures_by_direction.setdefault(direction_name, []).extend([
                {
                    "trip_id": row.trip_id,
                    "departure_time": row.departure_ts,
                    "type": "Scheduled"
                }
                for row in group.itertuples()
            ])

        # Ordenar cada lista de salidas por departure_time
        for direction, trips in departures_by_direction.items():
            trips.sort(key=lambda x: x["departure_time"])

        # Ordenar las claves del dict alfabéticamente
        departures_by_direction = dict(sorted(departures_by_direction.items(), key=lambda x: x[0]))

        log(f"Salidas agrupadas por dirección para {station_name} ({line_name}): {departures_by_direction}")
        return departures_by_direction