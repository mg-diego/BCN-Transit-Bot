from dataclasses import dataclass
from typing import Optional

@dataclass
class BicingStation:
    id: str
    type: str
    latitude: float
    longitude: float
    streetName: str
    streetNumber: str
    slots: int
    bikes: int
    type_bicing: int
    electrical_bikes: int
    mechanical_bikes: int
    status: int
    disponibilidad: int
    icon: str
    transition_start: Optional[str]
    transition_end: Optional[str]
    obcn: str

    def __post_init__(self):
        self.streetName = self.streetName.title()
