from dataclasses import dataclass
from datetime import datetime
import html
from typing import List

from domain import NextTrip

@dataclass
class RodaliesLineRoute:
    line_name: str
    code: str
    destination: str
    next_rodalies: List[NextTrip]

    EMOJIS = {
        "R1": "🟦", "R2": "🟩", "R2 Nord": "🟩", "R2 Sud": "🟩",
        "R3": "🟥", "R4": "🟨", "R7": "⬜", "R8": "🟪",
        "R11": "🟦", "R13": "⬛", "R14": "🟪", "R15": "🟫",
        "R16": "🟥", "R17": "🟧", "RG1": "🟦", "RT1": "🟦",
        "RT2": "⬜", "RL3": "🟩", "RL4": "🟨",
    }

    def __post_init__(self):
        self.line_name = f"{self.EMOJIS.get(self.line_name, '')} {self.line_name}"

    def __str__(self):
        header = f"     <b>{self.line_name} → {html.escape(self.destination)}</b>"

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        tram_info = "\n".join(
            self._format_rodalies_info(i, rodalies, number_emojis)
            for i, rodalies in enumerate(self.next_rodalies[:3])
        )

        return f"{header}\n{tram_info}"
    
    def _format_rodalies_info(self, i, rodalies: NextTrip, number_emojis):
        """Formatea la información de cada tren de Rodalies."""
        number_emoji = number_emojis[i] if i < len(number_emojis) else f"{i+1}."

        # Vía si existe
        via_text = f" | Vía {rodalies.platform} · {rodalies.id})" if rodalies.platform else ""

        # Horas programada y estimada
        scheduled_time = rodalies.scheduled_arrival()
        scheduled = scheduled_time.strftime("%H:%M") if scheduled_time else "?"
        estimated = datetime.fromtimestamp(rodalies.arrival_time).strftime("%H:%M") if rodalies.arrival_time else "?"

        # Retraso
        if rodalies.delay_in_minutes is None or rodalies.delay_in_minutes == 0:
            delay_text = ""
        if rodalies.delay_in_minutes > 0 and rodalies.delay_in_minutes < 15:
            delay_text = f"(+{rodalies.delay_in_minutes}m❗)"
        if rodalies.delay_in_minutes >= 15:
            delay_text = f"(+{rodalies.delay_in_minutes}m‼️)"
        if rodalies.delay_in_minutes < 0:
            delay_text = f"({rodalies.delay_in_minutes}m ⏪)"
        
        if scheduled in rodalies.remaining_time() and delay_text == "":
            return (
                f"           <i>{number_emoji} {rodalies.remaining_time()}{via_text}</i>\n"
            )
        else:  
            return (
                f"           <i>{number_emoji} {rodalies.remaining_time()}{via_text}</i>\n"
                f"                ⏰ {scheduled}{"" if delay_text == "" else f" → {estimated} {delay_text}"}"
            )
