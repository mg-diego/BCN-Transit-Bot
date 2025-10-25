from dataclasses import dataclass
from domain.common.line import Line
from domain.transport_type import TransportType
@dataclass
class TramLine(Line):

    @staticmethod
    def create_tram_line(props: dict):
        return Line(
            id=str(props.get('id', '')),
            code=str(props.get('code', '')),
            name=props.get('name', ''),
            description='TBD',
            origin='',
            destination='',
            color="008E78",
            transport_type=TransportType.TRAM
        )
    
    @staticmethod
    def create_tram_connection(props: dict):
        return Line(
            id=str(props.get('ID_LINIA', '')),
            code=str(props.get('CODI_LINIA', '')),
            name=props.get('NOM_LINIA', ''),
            description=props.get('DESC_LINIA', ''),
            origin=props.get('ORIGEN_LINIA', ''),
            destination=props.get('DESTI_LINIA', ''),
            color="008E78",
            transport_type=TransportType.TRAM
        )
    
    @staticmethod
    def create_tram_connection(id, code, name, description, origin, destination):
        return Line(
            id=id,
            code=code,
            name=name,
            description=description,
            origin=origin,
            destination=destination,
            color="008E78",
            transport_type=TransportType.TRAM
        )