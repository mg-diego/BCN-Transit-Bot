from dataclasses import dataclass
from domain.common.line import Line
from domain.transport_type import TransportType

@dataclass
class BusLine(Line):
    category: str

    @staticmethod
    def create_bus_line(feature: dict):
        props = feature['properties']
        return BusLine(
            id=str(props.get('ID_LINIA', '')),
            code=str(props.get('CODI_LINIA', '')),
            name=props.get('NOM_LINIA', ''),
            description=props.get('DESC_LINIA', ''),
            origin=props.get('ORIGEN_LINIA', ''),
            destination=props.get('DESTI_LINIA', ''),
            color=props.get('COLOR_LINIA', ''),
            category=props.get('NOM_FAMILIA', ''),
            transport_type=TransportType.BUS
        )
