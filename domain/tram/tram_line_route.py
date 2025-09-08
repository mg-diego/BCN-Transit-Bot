from collections import defaultdict
from dataclasses import dataclass
import html
from typing import List

from domain import NextTrip

    
@dataclass
class TramLineRoute:
    line_name: str
    code: str
    stop_name: str
    destination: str
    next_trams: List[NextTrip]

    def __str__(self):
        # Para un único objeto, mantenemos el formato original
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        header = f"     <b>🟩  {self.line_name} → {html.escape(self.destination)}</b>"
        tram_info = "\n".join(
            f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {tram.remaining_time()}</i>"
            for i, tram in enumerate(self.next_trams[:5])
        )
        return f"{header}\n{tram_info}"

    @staticmethod
    def group_by_line(routes: List["TramLineRoute"]) -> str:
        """Genera un string agrupado por line_name para varias rutas."""
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        grouped_routes = defaultdict(list)
        for route in routes:
            grouped_routes[route.line_name].append(route)

        lines = []
        for line_name, routes in grouped_routes.items():
            for route in routes:
                header = f"     <b>🟩  {line_name} → {html.escape(route.destination)}</b>"
                tram_info = "\n".join(
                    f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {tram.remaining_time()}</i>"
                    for i, tram in enumerate(route.next_trams[:5])
                )
                lines.append(f"{header}\n{tram_info}")
            lines.append("\n")

        return "\n".join(lines)

