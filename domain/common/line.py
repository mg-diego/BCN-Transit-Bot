from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from domain.common.alert import Alert
from domain.transport_type import TransportType

@dataclass
class Line:
    id: int
    code: int
    name: str
    description: str
    origin: str
    destination: str
    color: str
    transport_type: TransportType
    name_with_emoji: Optional[str] = None
    has_alerts: Optional[bool] = False
    alerts: Optional[list[Alert]] = field(default_factory=lambda: defaultdict(list))

    def __post_init__(self):
        if self.transport_type == TransportType.METRO:
            emojis = {
                "L1": "🟥",
                "L2": "🟪",
                "L3": "🟩",
                "L4": "🟨",
                "L5": "🟦",
                "L9N": "🟧",
                "L9S": "🟧",
                "L10N": "🟦",
                "L10S": "🟦",
                "L11": "🟩",
            }
        if self.transport_type == TransportType.TRAM:
            emojis = {
                "T1": "🟩",
                "T2": "🟩",
                "T3": "🟩",
                "T4": "🟩",
                "T5": "🟩",
                "T6": "🟩"
            }
        if self.transport_type == TransportType.FGC:
            emojis = {
                #Barcelona – Vallés
                "L1": "🟥",
                "S1": "🟥",
                "S2": "🟩",
                "L6": "🟪",
                "L7": "🟫",
                "L12": "🟪",

                #Llobregat – Anoia
                "L8": "🟪",
                "S3": "🟦",
                "S4": "🟨",
                "S8": "🟦",
                "S9": "🟥",
                "R5": "🟦",
                "R50": "🟦",
                "R6": "⬛",
                "R60": "⬛",
                "R63": "⬛",

                #Lleida – La Pobla de Segur
                "RL1": "🟩",
                "RL2": "🟩"
            }
        emoji = emojis.get(self.name, "")
        self.name_with_emoji = f"{emoji} {self.name}"


