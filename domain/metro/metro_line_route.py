from dataclasses import dataclass
from typing import List
import html

from domain import NextTrip

@dataclass
class MetroLineRoute:
    codi_linia: int
    nom_linia: str
    color_linia: str
    codi_trajecte: str
    desti_trajecte: str
    propers_trens: List[NextTrip]

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

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        tren_info = "\n".join(
            f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {tren.remaining_time()}</i>"
            for i, tren in enumerate(self.propers_trens[:5])
        )
        
        return f"{header}\n{tren_info}"
