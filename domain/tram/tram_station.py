from dataclasses import dataclass
from domain.common.line import Line
from domain.common.station import Station

@dataclass
class TramStation(Station):
    outboundCode: int
    returnCode: int

    @staticmethod
    def create_tram_station(props: dict):
        return TramStation(
            id=props.get('id', ''),
            code=props.get('gtfsCode',''),
            name=props.get('name', ''),
            order=props.get('order', ''),
            outboundCode=props.get('outboundCode', ''),
            returnCode=props.get('returnCode', ''),
            description=props.get('description', ''),
            latitude=props.get('latitude', ''),
            longitude=props.get('longitude', '')
        )
    
    @staticmethod
    def update_line_info(tram_station: Station, line: Line):
        tram_station.line_name_with_emoji = line.name_with_emoji
        tram_station.line_name = line.name
        tram_station.line_id = line.id
        tram_station.line_color = line.color
        return tram_station