from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional

from domain.common.alert import Alert
from .rodalies_station import RodaliesStation

@dataclass
class RodaliesLine:
    id: str
    name: str
    color: str = field(init=False)
    description: str
    type: str
    order_number: int
    origin_station_id: int
    origin_station_name: str
    destination_station_id: int
    destination_station_name: str
    stations: List[RodaliesStation]
    color: str = field(init=False)
    has_alerts: Optional[bool] = False
    alerts: Optional[list[Alert]] = field(default_factory=lambda: defaultdict(list))

    EMOJIS = {
        "R1": "🟦",
        "R2": "🟩",
        "R2 Nord": "🟩",
        "R2 Sud": "🟩",
        "R3": "🟥",
        "R4": "🟨",
        "R7": "⬜",
        "R8": "🟪",
        "R11": "🟦",
        "R13": "⬛",
        "R14": "🟪",
        "R15": "🟫",
        "R16": "🟥",
        "R17": "🟧",
        "RG1": "🟦",
        "RT1": "🟦",
        "RT2": "⬜",
        "RL3": "🟩",
        "RL4": "🟨",
    }

    COLORS = {
        "R1": "73B0DF",
        "R2": "009640",
        "R2 Nord": "AACB2B",
        "R2 Sud": "005F27",
        "R3": "E63027",
        "R4": "F6A22D",
        "R7": "BC79B2",
        "R8": "870064",
        "R11": "0064A7",
        "R13": "E8308A",
        "R14": "5E4295",
        "R15": "9A8B75",
        "R16": "B20933",
        "R17": "E87200",
        "RG1": "0071CE",
        "RT1": "00C4B3",
        "RT2": "E577CB",
        "RL3": "949300",
        "RL4": "FFDD00",
    }


    def __post_init__(self):
        emoji = self.EMOJIS.get(self.name, "❓")
        color = self.COLORS.get(self.name, "808080")
        self.emoji_name = f"{emoji} {self.name}"
        self.color = color

def create_rodalies_line(line, stations):
    return RodaliesLine(
                id=line["id"],
                name=line["name"],
                description=line["journeyDescription"],
                type=line["type"]["id"],
                order_number=line["orderNumber"],
                origin_station_id=line["originStation"]["id"],
                origin_station_name=line["originStation"]["name"],
                destination_station_id=line["destinationStation"]["id"],
                destination_station_name=line["destinationStation"]["name"],
                stations=stations
            )
