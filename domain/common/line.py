from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from domain.common.alert import Alert

@dataclass
class Line:
    id: int
    code: int
    name: str
    description: str
    origin: str
    destination: str
    color: str
    name_with_emoji: Optional[str] = None
    has_alerts: Optional[bool] = False
    alerts: Optional[list[Alert]] = field(default_factory=lambda: defaultdict(list))

    def __post_init__(self):
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
        emoji = emojis.get(self.name, "")
        self.name_with_emoji = f"{emoji} {self.name}"


