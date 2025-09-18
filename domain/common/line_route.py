from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import html

from domain import NextTrip
from domain.transport_type import TransportType

@dataclass
class LineRoute:
    route_id: str
    line_type: TransportType
    line_name: str
    color: str
    destination: str
    next_trips: List[NextTrip]
    name_with_emoji: Optional[str] = ""
    line_id: Optional[str] = ""    
    line_code: Optional[str] = ""

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
        elif self.line_type == TransportType.BUS:
            emojis = {
                "H": "🟦",
                "D": "🟪",
                "V": "🟩",
                "M": "🔴",
                "X": "🟨",
                "N": "🟦"
            }
            for letter in self.line_name:
                if letter in emojis:
                    self.name_with_emoji = f"{emojis[letter]} {self.line_name}"
                    break
            else:
                if self.line_name.isdigit():
                    self.name_with_emoji = f"🔴 {self.line_name}"
            return
        elif self.line_type == TransportType.FGC:
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
        elif self.line_type == TransportType.RODALIES:
            emojis = {
                "R1": "🟦", "R2": "🟩", "R2 Nord": "🟩", "R2 Sud": "🟩",
                "R3": "🟥", "R4": "🟨", "R7": "⬜", "R8": "🟪",
                "R11": "🟦", "R13": "⬛", "R14": "🟪", "R15": "🟫",
                "R16": "🟥", "R17": "🟧", "RG1": "🟦", "RT1": "🟦",
                "RT2": "⬜", "RL3": "🟩", "RL4": "🟨",
            }

        emoji = emojis.get(self.line_name, "")
        self.name_with_emoji = f"{emoji} {self.line_name}"

    @staticmethod
    def simple_list(route, arriving_threshold=40, default_msg: str = '') -> str:
        header = f"     <b>{route.name_with_emoji} → {html.escape(route.destination)}</b>"

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        tren_info = "\n".join(
            f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {trip.remaining_time(arriving_threshold)}</i>"
            for i, trip in enumerate(route.next_trips[:5])
        )
        if tren_info == "":
            tren_info = default_msg
        
        return f"{header}\n{tren_info}"
    @staticmethod
    def grouped_list(routes, default_msg: str = '') -> str:
        """Genera un string agrupado por line_name para varias rutas."""
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        grouped_routes = defaultdict(list)
        for route in routes:
            grouped_routes[route.line_name].append(route)

        lines = []
        for routes in grouped_routes.values():
            for route in routes:
                header = f"     <b>{route.name_with_emoji} → {html.escape(route.destination)}</b>"
                tram_info = "\n".join(
                    f"           <i>{number_emojis[i] if i < len(number_emojis) else f'{i+1}.'} {tram.remaining_time()}</i>"
                    for i, tram in enumerate(route.next_trips[:5])
                )
                if tram_info == "":
                    tram_info = default_msg
                lines.append(f"{header}\n{tram_info}")
            lines.append("\n")

        return "\n".join(lines)   
    
    
    @staticmethod
    def scheduled_list(route, with_arrival_date=True, default_msg: str = '') -> str:
        header = f"     <b>{route.name_with_emoji} → {html.escape(route.destination)}</b>"
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        trips_info = []
        for i, trip in enumerate(route.next_trips[:3]):
            number_emoji = number_emojis[i] if i < len(number_emojis) else f"{i + 1}."

            # Vía y número de tren si existen
            via_text = f" | Vía {trip.platform}" if trip.platform else ""

            # Horas programada y estimada
            scheduled_time = trip.scheduled_arrival()
            scheduled = scheduled_time.strftime("%H:%Mh") if scheduled_time else "?"
            estimated = (
                datetime.fromtimestamp(trip.arrival_time).strftime("%H:%Mh")
                if trip.arrival_time
                else "?"
            )

            # Retraso
            delay_text = ""
            if trip.delay_in_minutes is not None:
                if trip.delay_in_minutes > 0:
                    if trip.delay_in_minutes >= 15:
                        delay_text = f"(+{trip.delay_in_minutes}m‼️)"
                    else:
                        delay_text = f"(+{trip.delay_in_minutes}m❗)"
                elif trip.delay_in_minutes < 0:
                    delay_text = f"({trip.delay_in_minutes}m ⏪)"

            # Tiempo restante
            remaining = trip.remaining_time_and_arrival_date() if with_arrival_date else trip.remaining_time()

            # Si la hora programada ya está incluida en remaining y no hay retraso → mostrar versión simple
            if scheduled in remaining and delay_text == "":
                trips_info.append(
                    f"           <i>{number_emoji} {remaining}{via_text}</i>"
                )
            else:
                trips_info.append(
                    f"           <i>{number_emoji} {remaining}{via_text}</i>\n"
                    f"                ⏰ {scheduled}"
                    f"{'' if delay_text == '' else f' → {estimated} {delay_text}'}"
                )

        return f"{header}\n" + "\n".join(trips_info)