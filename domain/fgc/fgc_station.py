from dataclasses import dataclass
from typing import Optional
from domain.common.station import Station
from domain.fgc.fgc_line import FgcLine

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
    
    @staticmethod
    def update_line_info(fgc_station: Station, line: FgcLine):
        fgc_station.line_name_with_emoji = line.name_with_emoji
        fgc_station.line_color = line.color
        fgc_station.line_id = line.id
        fgc_station.line_name = line.name
        fgc_station.line_code = line.id
        
        return fgc_station