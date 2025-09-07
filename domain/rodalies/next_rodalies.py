import html
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

SPAIN_TZ = ZoneInfo("Europe/Madrid")


@dataclass
class NextRodalies:
    id: str
    arrival_time: datetime  # Hora programada
    delay_in_minutes: int
    platform: str = field(default_factory=str)

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
            return "🔜"

        hours, remainder = divmod(int(remaining_sec), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f" {hours}h {minutes}m {seconds}s"
        else:
            return f" {minutes}m {seconds}s"

    def scheduled_arrival(self) -> datetime:
        """Devuelve la hora programada de llegada en base al retraso."""
        if not self.arrival_time:
            return None
        return self.arrival_time - timedelta(minutes=self.delay_in_minutes or 0)


@dataclass
class RodaliesLineRoute:
    line_name: str
    code: str
    destination: str
    next_rodalies: List[NextRodalies] = field(default_factory=list)

    EMOJIS = {
        "R1": "🟦",
        "R2": "🟩",
        "R2 Nord": "🟩",
        "R2 Sud": "🟩",
        "R3": "🟥",
        "R4": "🟨",
        "R7": "⬜",
        "R8": "🟪",
        "R11": "🟦",
        "R13": "⬛",
        "R14": "🟪",
        "R15": "🟫",
        "R16": "🟥",
        "R17": "🟧",
        "RG1": "🟦",
        "RT1": "🟦",
        "RT2": "⬜",
        "RL3": "🟩",
        "RL4": "🟨",
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

    def _format_rodalies_info(self, i, rodalies: NextRodalies, number_emojis):
        """Formatea la información de cada tren de Rodalies."""
        number_emoji = number_emojis[i] if i < len(number_emojis) else f"{i+1}."

        # Vía si existe
        via_text = (
            f" (Vía {rodalies.platform} - {rodalies.id})" if rodalies.platform else ""
        )

        # Horas programada y estimada
        scheduled_time = rodalies.scheduled_arrival()
        scheduled = scheduled_time.strftime("%H:%M") if scheduled_time else "?"
        estimated = (
            rodalies.arrival_time.strftime("%H:%M") if rodalies.arrival_time else "?"
        )

        # Retraso
        if rodalies.delay_in_minutes is None or rodalies.delay_in_minutes == 0:
            delay_text = ""
        if rodalies.delay_in_minutes > 0 and rodalies.delay_in_minutes < 15:
            delay_text = f"(+{rodalies.delay_in_minutes}m❗)"
        if rodalies.delay_in_minutes >= 15:
            delay_text = f"(+{rodalies.delay_in_minutes}m‼️)"
        if rodalies.delay_in_minutes < 0:
            delay_text = f"({rodalies.delay_in_minutes}m ⏪)"

        return (
            f"           <i>{number_emoji} {rodalies.remaining_from_now()}{via_text}</i>\n"
            f"                ⏰ {scheduled} → {estimated} {delay_text}"
        )
