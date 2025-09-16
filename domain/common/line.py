from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from domain.common.alert import Alert
from domain.transport_type import TransportType

@dataclass(kw_only=True)
class Line:
    id: str
    code: str
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
        if self.transport_type == TransportType.RODALIES:
            emojis = {
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

        emoji = emojis.get(self.name, "")
        self.name_with_emoji = f"{emoji} {self.name}"

        if self.color is None:
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
            self.color = COLORS.get(self.name, self.color or "808080")


