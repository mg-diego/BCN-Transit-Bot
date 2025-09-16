from dataclasses import dataclass
from domain.common.line import Line
from domain.transport_type import TransportType
@dataclass
class TramLine(Line):

    @staticmethod
    def create_tram_line(props: dict):
        return Line(
            id=props.get('id', ''),
            code=props.get('code', ''),
            name=props.get('name', ''),
            description='TBD',
            origin=None,
            destination=None,
            color="008E78",
            transport_type=TransportType.TRAM
        )