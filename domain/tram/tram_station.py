from dataclasses import dataclass
from domain.common.station import Station

@dataclass
class TramStation(Station):
    outboundCode: int
    returnCode: int

def create_tram_station(props: dict) -> TramStation:
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