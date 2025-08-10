import json
import base64

class Mapper:

    def map_metro_stations(self, stations):
        data = {
            "stops": [
                {
                    "lat": station.coordinates[1],
                    "lon": station.coordinates[0],
                    "name": station.NOM_ESTACIO
                }
                for station in stations
            ]
        }

        json_str = json.dumps(data)
        encoded_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        print(encoded_str)

        return encoded_str