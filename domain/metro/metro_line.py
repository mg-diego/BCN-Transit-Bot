from dataclasses import dataclass
from domain.common.line import Line
from domain.transport_type import TransportType

@dataclass
class MetroLine(Line):

    @staticmethod
    def create_metro_line(feature: dict):
        props = feature['properties']
        return Line(
            id=props.get('ID_LINIA', ''),
            code=props.get('CODI_LINIA', ''),
            name=props.get('NOM_LINIA', ''),
            description=props.get('DESC_LINIA', ''),
            origin=props.get('ORIGEN_LINIA', ''),
            destination=props.get('DESTI_LINIA', ''),
            color=props.get('COLOR_LINIA', ''),
            transport_type=TransportType.METRO
        )