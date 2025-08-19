from dataclasses import dataclass
from typing import Dict
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
    original_name: Optional[str] = None

    def __post_init__(self):
        self.original_name = self.name
        self.name = f"🟩 {self.original_name}"

    def __str__(self):
        return f"TramLine {self.name} (code: {self.code}) in network {self.network['name']}"