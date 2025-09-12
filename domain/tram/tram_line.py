from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict
from domain.common.alert import Alert
from domain.tram.tram_network import TramNetwork
from typing import Optional

@dataclass
class TramLine:
    id: int
    name: str
    description: Dict[str, str]
    network: TramNetwork
    code: int
    image: str
    color: str = "008E78"
    original_name: Optional[str] = None
    has_alerts: Optional[bool] = False
    alerts: Optional[list[Alert]] = field(default_factory=lambda: defaultdict(list))

    def __post_init__(self):
        self.original_name = self.name
        self.name = f"🟩 {self.original_name}"

    def __str__(self):
        return f"TramLine {self.name} (code: {self.code}) in network {self.network.name}"