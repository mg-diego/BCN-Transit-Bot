from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional
import html

from domain import NextTrip
from domain.transport_type import TransportType

@dataclass
class LineRoute:
    route_id: str
    line_type: TransportType
    name: str
    color: str
    destination: str
    next_trips: List[NextTrip]
    name_with_emoji: Optional[str] = ""
    line_id: Optional[str] = ""
    line_name: Optional[str] = ""

    def __post_init__(self):
        if self.line_type == TransportType.METRO:
            emojis = {
                "L1": "🟥",
                "L2": "🟪",
                "L3": "🟩",
                "L4": "🟨",
                "L5": "🟦",
                "L9S": "🟧",
                "L9N": "🟧",
            }
        elif self.line_type == TransportType.TRAM:
            emojis = {
                "T1": "🟩",
                "T2": "🟩",
                "T3": "🟩",
                "T4": "🟩",
                "T5": "🟩",
                "T6": "🟩"
            }
        emoji = emojis.get(self.name, "")
        self.name_with_emoji = f"{emoji} {self.name}"

    @staticmethod
    def simple_list(route):
        header = f"     <b>{route.name_with_emoji} → {html.escape(route.destination)}</b>"

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        tren_info = "\n".join(
            f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {trip.remaining_time()}</i>"
            for i, trip in enumerate(route.next_trips[:5])
        )
        
        return f"{header}\n{tren_info}"
    
    @staticmethod
    def grouped_list(routes) -> str:
        """Genera un string agrupado por line_name para varias rutas."""
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        grouped_routes = defaultdict(list)
        for route in routes:
            grouped_routes[route.name_with_emoji].append(route)

        lines = []
        for line_name, routes in grouped_routes.items():
            for route in routes:
                header = f"     <b>🟩  {line_name} → {html.escape(route.destination)}</b>"
                tram_info = "\n".join(
                    f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {tram.remaining_time()}</i>"
                    for i, tram in enumerate(route.next_trips[:5])
                )
                lines.append(f"{header}\n{tram_info}")
            lines.append("\n")

        return "\n".join(lines)
