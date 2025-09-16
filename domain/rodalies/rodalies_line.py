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
            id=line["id"],
            code=line["id"],
            name=line["name"],
            description=line["journeyDescription"],
            transport_type=TransportType.RODALIES,
            origin=line["originStation"]["name"],
            destination=line["destinationStation"]["name"],
            stations=stations,
            color=None
        )
