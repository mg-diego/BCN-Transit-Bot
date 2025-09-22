from dataclasses import dataclass
from typing import List

from domain.transport_type import TransportType

from .rodalies_station import RodaliesStation
from domain.common.line import Line
@dataclass
class RodaliesLine(Line):
    stations: List[RodaliesStation]

    @staticmethod
    def create_rodalies_line(line, stations):
        return RodaliesLine(
            id=str(line["id"]),
            code=str(line["id"]),
            name=line["name"],
            description=line["journeyDescription"],
            transport_type=TransportType.RODALIES,
            origin=line["originStation"]["name"],
            destination=line["destinationStation"]["name"],
            stations=stations,
            color=None
        )
    
    @staticmethod
    def create_rodalies_connection(line):
        return RodaliesLine(
            id=str(line.get('ID_LINIA', '')),
            code=str(line.get('CODI_LINIA', '')),
            name=str(line.get('NOM_LINIA', '')),
            description=str(line.get('DESC_LINIA', '')),
            transport_type=TransportType.RODALIES,
            origin=line.get('DESC_LINIA').split("-")[0].strip() if line.get('DESC_LINIA') and "-" in line.get('DESC_LINIA') else '',
            destination=line.get('DESC_LINIA').split("-")[1].strip() if line.get('DESC_LINIA') and "-" in line.get('DESC_LINIA') else '',
            stations=[],
            color=str(line.get('COLOR_LINIA', '')),
        )
