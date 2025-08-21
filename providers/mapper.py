import json
import html
from typing import List
from domain.bus.bus_stop import BusStop
from domain.metro.metro_station import MetroStation
from domain.tram.tram_stop import TramStop
import lzstring
import unicodedata

class Mapper:

    def _normalize_name(self, name: str) -> str:
    # Elimina acentos y normaliza caracteres especiales
        return ''.join(
            c for c in unicodedata.normalize('NFKD', name)
            if not unicodedata.combining(c)
        )

    def map_metro_stations(self, stations: List[MetroStation], line_id, line_name):
        lz = lzstring.LZString()

        stops = []
        for station in stations:
            stops.append({
                "lat": station.coordinates[1],
                "lon": station.coordinates[0],
                "name": f"{station.CODI_ESTACIO} - {self._normalize_name(station.NOM_ESTACIO)}",
                "color": station.COLOR_LINIA,
                "direction": station.DESTI_SERVEI
            })
        for station in reversed(stations):
            stops.append({
                "lat": station.coordinates[1],
                "lon": station.coordinates[0],
                "name": f"{station.CODI_ESTACIO} - {self._normalize_name(station.NOM_ESTACIO)}",
                "color": station.COLOR_LINIA,
                "direction": station.ORIGEN_SERVEI
            })

        data = {
            "type": "metro",
            "line_id": line_id,
            "line_name": html.escape(line_name),
            "stops": stops
        }

        json_str = json.dumps(data)
        compressed = lz.compressToEncodedURIComponent(json_str)
        return compressed
    
    def map_bus_stops(self, stops: List[BusStop], line_id, line_name):        
        lz = lzstring.LZString()
        data = {
            "type": "bus",
            "line_id": line_id,
            "line_name": html.escape(line_name),
            "stops": [
                {
                    "lat": stop.coordinates[1],
                    "lon": stop.coordinates[0],
                    "name": f"{stop.CODI_PARADA} - {self._normalize_name(stop.NOM_PARADA)}",
                    "color": stop.COLOR_REC,
                    "direction": stop.DESTI_SENTIT
                }
                for stop in stops
            ]
        }

        json_str = json.dumps(data)
        compressed = lz.compressToEncodedURIComponent(json_str)
        return compressed
    
    def map_tram_stops(self, stops: List[TramStop], line_id, line_name):
        lz = lzstring.LZString()
        origin = stops[0].name
        destination = stops[-1].name

        tram_stops = []
        for stop in stops:
            tram_stops.append({
                "lat": stop.latitude,
                "lon": stop.longitude,
                "name": f"{stop.id} - {self._normalize_name(stop.name)}",
                "color": "008E78",
                "direction": destination
            })
        for stop in reversed(stops):
            tram_stops.append({
                "lat": stop.latitude,
                "lon": stop.longitude,
                "name": f"{stop.id} - {self._normalize_name(stop.name)}",
                "color": "008E78",
                "direction": origin
            })

        data = {
            "type": "metro",
            "line_id": line_id,
            "line_name": html.escape(line_name),
            "stops": tram_stops
        }

        json_str = json.dumps(data)
        compressed = lz.compressToEncodedURIComponent(json_str)
        return compressed