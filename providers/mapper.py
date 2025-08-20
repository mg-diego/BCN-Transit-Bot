import json
from typing import List
from domain.bus.bus_stop import BusStop
from domain.metro.metro_station import MetroStation
import lzstring

class Mapper:

    def map_metro_stations(self, stations: List[MetroStation], line_id, line_name):
        lz = lzstring.LZString()

        stops = []
        for station in stations:
            # Dirección hacia el destino
            stops.append({
                "lat": station.coordinates[1],
                "lon": station.coordinates[0],
                "name": f"{station.CODI_ESTACIO} - {station.NOM_ESTACIO}",
                "color": station.COLOR_LINIA,
                "direction": station.DESTI_SERVEI
            })
            # Dirección hacia el origen
            stops.append({
                "lat": station.coordinates[1],
                "lon": station.coordinates[0],
                "name": f"{station.CODI_ESTACIO} - {station.NOM_ESTACIO}",
                "color": station.COLOR_LINIA,
                "direction": station.ORIGEN_SERVEI
            })

        data = {
            "type": "metro",
            "line_id": line_id,
            "line_name": line_name,
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
            "line_name": line_name,
            "stops": [
                {
                    "lat": stop.coordinates[1],
                    "lon": stop.coordinates[0],
                    "name": f"{stop.CODI_PARADA} - {stop.NOM_PARADA}",
                    "color": stop.COLOR_REC,
                    "direction": stop.DESTI_SENTIT
                }
                for stop in stops
            ]
        }

        json_str = json.dumps(data)
        compressed = lz.compressToEncodedURIComponent(json_str)
        return compressed