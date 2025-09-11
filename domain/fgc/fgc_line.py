from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from domain.common.alert import Alert

@dataclass
class FgcLine:
    id: int
    name: str
    description: str
    origin: str
    destination: str
    type: int
    color: str
    name_with_emoji: Optional[str] = None
    has_alerts: Optional[bool] = False
    alerts: Optional[list[Alert]] = field(default_factory=lambda: defaultdict(list))

def _set_emoji_at_name(name):
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
    emoji = emojis.get(name, "")
    return f"{emoji} {name}"

def create_fgc_line(line: dict) -> FgcLine:
    return FgcLine(
        id = line.get('route_id'),
        name = line.get('route_short_name'),
        description = line.get('route_long_name'),
        origin = line.get('route_long_name').split("-")[0].strip() if "-" in line.get('route_long_name') else '',
        destination = line.get('route_long_name').split("-")[1].strip() if "-" in line.get('route_long_name') else '',
        type = line.get('route_type'),
        color = line.get('route_color'),
        name_with_emoji = _set_emoji_at_name(line.get('route_short_name'))
    )