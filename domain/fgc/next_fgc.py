from dataclasses import dataclass
from typing import List
from datetime import datetime
import html

@dataclass
class NextFgc:
    codi_servei: str
    temps_arribada: int  # Epoch en segundos

    def arrival_time_str(self) -> str:
        now = datetime.now().timestamp()
        delta_s = self.temps_arribada - now

        if delta_s <= 40:
            return "🔜"

        minutes, seconds = divmod(int(delta_s), 60)

        parts = []
        if minutes:
            parts.append(f"{minutes}min")
        if seconds or not minutes:
            parts.append(f"{seconds}s")

        return " ".join(parts)

@dataclass
class FgcLineRoute:
    codi_linia: int
    nom_linia: str
    color_linia: str
    codi_trajecte: str
    desti_trajecte: str
    propers_trens: List[NextFgc]

    def __post_init__(self):
        emojis = {
            #Barcelona – Vallés
            "L1": "🟥",
            "S1": "🟥",
            "S2": "🟩",
            "L6": "🟪",
            "L7": "🟫",
            "L12": "🟪",

            #Llobregat – Anoia
            "L8": "🟪",
            "S3": "🟦",
            "S4": "🟨",
            "S8": "🟦",
            "S9": "🟥",
            "R5": "🟦",
            "R50": "🟦",
            "R6": "⬛",
            "R60": "⬛",

            #Lleida – La Pobla de Segur
            "RL1": "🟩",
            "RL2": "🟩"
        }
        emoji = emojis.get(self.nom_linia, "")
        self.nom_linia = f"{emoji} {self.nom_linia}"

    def __str__(self):
        header = f"     <b>{self.nom_linia} → {html.escape(self.desti_trajecte)}</b>"

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        tren_info = "\n".join(
            f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {tren.arrival_time_str()}</i>"
            for i, tren in enumerate(self.propers_trens[:5])
        )
        
        return f"{header}\n{tren_info}"