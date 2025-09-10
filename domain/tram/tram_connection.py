from dataclasses import dataclass
from typing import List

@dataclass
class TramStationConnection:
    stopId: int
    connectionId: int
    order: int

@dataclass
class TramConnection:
    id: int
    name: str
    latitude: float
    longitude: float
    order: int
    image: str
    stopConnections: List[TramStationConnection]

    def __str__(self):
        emojis = {
            "L1": "🟥",
            "L2": "🟪",
            "L3": "🟩",
            "L4": "🟨",
            "L5": "🟦",
            "L9S": "🟧",
            "L9N": "🟧",
        }
        emoji = emojis.get(self.name, "")
        return f"     {emoji} {self.name}"