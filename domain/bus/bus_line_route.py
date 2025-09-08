from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import html

from domain import NextTrip

@dataclass
class BusLineRoute:
    id_operador: int
    transit_namespace: str
    codi_linia: int
    nom_linia: str
    id_sentit: int
    codi_trajecte: str
    desti_trajecte: str
    propers_busos: List[NextTrip]
    original_nom_linia: Optional[str] = None

    def __post_init__(self):
        emojis = {
            "H": "🟦",
            "D": "🟪",
            "V": "🟩",
            "M": "🔴",
            "X": "🟨"
        }

        self.original_nom_linia = self.nom_linia

        for letra in self.nom_linia:
            if letra in emojis:
                self.nom_linia = f"{emojis[letra]} {self.nom_linia}"
                break
        else:
            if self.nom_linia.isdigit():
                self.nom_linia = f"🔴 {self.nom_linia}"

    def __str__(self):
        header = f"     <b>{self.nom_linia} → {html.escape(self.desti_trajecte)}</b>"

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        bus_info = "\n".join(
            f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {bus.remaining_time(arriving_threshold=60)}</i>"
            for i, bus in enumerate(self.propers_busos[:5])
        )
        
        return f"{header}\n{bus_info}"
