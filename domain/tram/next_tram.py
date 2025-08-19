from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import html


@dataclass
class NextTram:
    vehicleId: str
    stopName: str
    code: int
    arrivalTime: datetime
    scheduledTime: datetime
    destination: str
    lineName: str
    occupancy: Optional[str]

    def arrival_time_str(self) -> str:
        arrival_time = datetime.strptime(self.arrivalTime, "%Y-%m-%d %H:%M:%S")
        delta = arrival_time - datetime.now()

        # Convertimos a segundos totales
        total_seconds = int(delta.total_seconds())

        if total_seconds <= 40:
            return "🔜 Entrando"

        minutes, seconds = divmod(total_seconds, 60)
        return f" {minutes}m {seconds}s"

    
@dataclass
class TramLineRoute:
    line_name: str
    destination: str
    next_trams: List[NextTram]

    def __str__(self):
        header = f"     <b>{self.line_name} → {html.escape(self.destination)}</b>"

        number_emojis = [
            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", 
            "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"
        ]

        tram_info = "\n".join(
            f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {tram.arrival_time_str()}</i>"
            for i, tram in enumerate(self.next_trams)
        )
        
        return f"{header}\n{tram_info}"

