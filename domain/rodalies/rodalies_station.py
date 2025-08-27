from dataclasses import dataclass
from typing import Optional

@dataclass
class RodaliesStation:
    id: str
    name: str
    latitude: float
    longitude: float
    is_accessible: bool
    line_id: Optional[int] = None
    line_name: Optional[int] = None

def create_rodalies_station(station_data):
    return RodaliesStation(
        id=station_data["id"],
        name=station_data["name"],
        latitude=station_data["latitude"],
        longitude=station_data["longitude"],
        is_accessible=station_data["accessible"]
    )