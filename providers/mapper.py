import json
import lzstring

class Mapper:

    def map_metro_stations(self, stations):
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
    
    def map_bus_stops(self, stops):        
        lz = lzstring.LZString()        
        data = {
            "stops": [
                {
                    "lat": stop.coordinates[1],
                    "lon": stop.coordinates[0],
                    "name": f"{stop.CODI_PARADA} - {stop.NOM_PARADA}",
                    "color": stop.COLOR_REC
                }
                for stop in stops
            ]
        }

        json_str = json.dumps(data)
        compressed = lz.compressToEncodedURIComponent(json_str)
        return compressed