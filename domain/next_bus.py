from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import html

@dataclass
class NextBus:
    temps_arribada: int
    id_bus: Optional[str] = None

    def arrival_time_str(self) -> str:
        now = datetime.now().timestamp() * 1000  # en ms
        delta_ms = self.temps_arribada - now

        if delta_ms <= 60000:
            return "🔜 Llegando"

        total_seconds = int(delta_ms / 1000)
        minutes, seconds = divmod(total_seconds, 60)

        parts = []
        if minutes:
            parts.append(f"{minutes}min")
        if seconds or not minutes:
            parts.append(f"{seconds}s")

        return " ".join(parts)

@dataclass
class BusLineRoute:
    id_operador: int
    transit_namespace: str
    codi_linia: int
    nom_linia: str
    id_sentit: int
    codi_trajecte: str
    desti_trajecte: str
    propers_busos: List[NextBus]
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

        number_emojis = [
            "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", 
            "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"
        ]

        bus_info = "\n".join(
            f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {bus.arrival_time_str()}</i>"
            for i, bus in enumerate(self.propers_busos)
        )
        
        return f"{header}\n{bus_info}"
