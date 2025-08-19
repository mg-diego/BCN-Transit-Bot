from dataclasses import dataclass
from typing import List
from datetime import datetime
import html

@dataclass
class NextMetro:
    codi_servei: str
    temps_arribada: int  # Epoch en milisegundos

    def arrival_time_str(self) -> str:
        now = datetime.now().timestamp() * 1000  # en ms
        delta_ms = self.temps_arribada - now

        if delta_ms <= 40000:
            return "🔜 Entrando"

        total_seconds = int(delta_ms / 1000)
        minutes, seconds = divmod(total_seconds, 60)

        parts = []
        if minutes:
            parts.append(f"{minutes}min")
        if seconds or not minutes:
            parts.append(f"{seconds}s")

        return " ".join(parts)

@dataclass
class MetroLineRoute:
    codi_linia: int
    nom_linia: str
    color_linia: str
    codi_trajecte: str
    desti_trajecte: str
    propers_trens: List[NextMetro]

    def __post_init__(self):
        emojis = {
            "L1": "🟥",
            "L2": "🟪",
            "L3": "🟩",
            "L4": "🟨",
            "L5": "🟦",
            "L9S": "🟧",
            "L9N": "🟧",
        }
        emoji = emojis.get(self.nom_linia, "")
        self.nom_linia = f"{emoji} {self.nom_linia}"

    def __str__(self):
        header = f"     <b>{self.nom_linia} → {html.escape(self.desti_trajecte)}</b>"

        number_emojis = [
            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", 
            "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"
        ]

        tren_info = "\n".join(
            f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {tren.arrival_time_str()}</i>"
            for i, tren in enumerate(self.propers_trens)
        )
        
        return f"{header}\n{tren_info}"
