from dataclasses import dataclass
from domain.common.line import Line
from domain.common.station import Station
from domain.transport_type import TransportType

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
            longitude=station_data["longitude"],
            transport_type=TransportType.RODALIES
        )
    
    @staticmethod
    def update_line_info(rodalies_station: Station, line: Line):
        rodalies_station.line_name_with_emoji = line.name_with_emoji
        rodalies_station.line_color = line.color
        rodalies_station.line_id = line.id
        rodalies_station.line_name = line.name
        rodalies_station.line_code = line.id