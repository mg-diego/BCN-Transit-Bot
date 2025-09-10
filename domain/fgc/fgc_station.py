from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional
from domain.common.station import Station

@dataclass
class FgcStation(Station):
    moute_id: Optional[int] =  None

    @staticmethod
    def create_fgc_station(station_data, line_name, order):
        return FgcStation(
            id=station_data["stop_id"],
            code=station_data["stop_id"],
            name=station_data["stop_name"],
            latitude=float(station_data["stop_lat"]),
            longitude=float(station_data["stop_lon"]),
            line_id=line_name,
            line_name=line_name,
            moute_id=station_data.get("moute_id"),
            order=order
        )