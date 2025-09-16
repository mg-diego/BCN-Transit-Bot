from dataclasses import dataclass

from domain.common.line import Line
from domain.transport_type import TransportType
@dataclass
class FgcLine(Line):

    @staticmethod
    def create_fgc_line(line: dict):
        return FgcLine(
            id = str(line.get('route_id')),
            code = str(line.get('route_id')),
            name = line.get('route_short_name'),
            description = line.get('route_long_name'),
            origin = line.get('route_long_name').split("-")[0].strip() if "-" in line.get('route_long_name') else '',
            destination = line.get('route_long_name').split("-")[1].strip() if "-" in line.get('route_long_name') else '',
            color = line.get('route_color'),
            transport_type=TransportType.FGC
        )