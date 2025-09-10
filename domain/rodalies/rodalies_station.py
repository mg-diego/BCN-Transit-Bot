from dataclasses import dataclass
from domain.common.station import Station

@dataclass
class RodaliesStation(Station):

    @staticmethod
    def create_rodalies_station(station_data):
        return RodaliesStation(
            id=station_data["id"],
            code=station_data["id"],
            order=None,
            name=station_data["name"],
            latitude=station_data["latitude"],
            longitude=station_data["longitude"]
        )