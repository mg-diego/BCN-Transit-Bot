import json
from typing import List
from domain.bus.bus_stop import BusStop
from domain.metro.metro_station import MetroStation
import lzstring

class Mapper:

    def map_metro_stations(self, stations: List[MetroStation]):
        lz = lzstring.LZString()
        data = {
            "stops": [
                {
                    "lat": station.coordinates[1],
                    "lon": station.coordinates[0],
                    "name": station.NOM_ESTACIO,
                    "color": station.COLOR_LINIA
                }
                for station in stations
            ]
        }

        json_str = json.dumps(data)
        compressed = lz.compressToEncodedURIComponent(json_str)
        return compressed
    
    def map_bus_stops(self, stops: List[BusStop], line_id):        
        lz = lzstring.LZString()        
        data = {
            "line_id": line_id,
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