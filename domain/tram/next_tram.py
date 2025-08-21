from dataclasses import dataclass, field
from datetime import datetime
import html
from typing import List
from zoneinfo import ZoneInfo

SPAIN_TZ = ZoneInfo("Europe/Madrid")

@dataclass
class NextTram:
    vehicle_id: str
    occupancy: str
    arrival_time: datetime

    def __str__(self):
        return f"arrivalTime: {self.remaining_from_now()}"

    def remaining_from_now(self) -> str:
        if not self.arrival_time:
            return "-"

        # Normalizamos la zona horaria de arrival_time
        if self.arrival_time.tzinfo is None:
            arrival_time = self.arrival_time.replace(tzinfo=SPAIN_TZ)
        else:
            arrival_time = self.arrival_time.astimezone(SPAIN_TZ)

        # Hora actual en la misma zona horaria
        now = datetime.now(SPAIN_TZ)
        remaining_sec = (arrival_time - now).total_seconds()

        if remaining_sec < 40:
            return "🔜 Entrando"

        hours, remainder = divmod(int(remaining_sec), 3600)
        minutes, seconds = divmod(remainder, 60)

        # Si faltan más de 1 hora, mostramos horas + minutos + segundos
        if hours > 0:
            return f" {hours}h {minutes}m {seconds}s"
        else:
            return f" {minutes}m {seconds}s"

    
@dataclass
class TramLineRoute:
    line_name: str
    code: str
    stop_name: str
    destination: str
    next_trams: List[NextTram] = field(default_factory=list)

    def __str__(self):
        header = f"     <b>🟩  {self.line_name} → {html.escape(self.destination)}</b>"

        number_emojis = [
            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", 
            "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"
        ]

        tram_info = "\n".join(
            f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {tram.remaining_from_now()}</i>"
            for i, tram in enumerate(self.next_trams)
        )
        
        return f"{header}\n{tram_info}"

