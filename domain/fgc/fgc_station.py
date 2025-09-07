from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FgcStation:
    id: str
    name: str
    lat: float
    lon: float
    line_id: str
    order: int
    has_alerts: Optional[bool] = False
    alerts: Optional[list] = field(default_factory=lambda: defaultdict(list))
    moute_id: Optional[int] = None
