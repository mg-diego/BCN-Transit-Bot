from dataclasses import dataclass
from typing import Optional

@dataclass
class TramStop:
    id: int
    name: str
    description: Optional[str]
    latitude: float
    longitude: float
    outboundCode: int
    returnCode: int
    gtfsCode: str
    order: int
    image: str
    lineId: Optional[int] = None 
    lineName: Optional[int] = None 

    def __str__(self):
        return f"TramStop {self.name} (code: {self.id} - outbound: {self.outboundCode} - return: {self.returnCode})"