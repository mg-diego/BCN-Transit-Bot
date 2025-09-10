from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

@dataclass(kw_only=True)
class Station:
    id: int
    code: int
    name: str
    latitude: float
    longitude: float
    order: int
    name_with_emoji: Optional[str] = None
    description: Optional[str] = None
    line_id: Optional[int] = None
    line_code: Optional[int] = None
    line_color: Optional[str] = None
    line_name: Optional[str] = None
    line_name_with_emoji: Optional[str] = None
    has_alerts: Optional[bool] = False
    alerts: Optional[list] = field(default_factory=lambda: defaultdict(list))