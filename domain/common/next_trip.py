from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SPAIN_TZ = ZoneInfo("Europe/Madrid")

@dataclass
class NextTrip:
    id: str
    arrival_time: int # Epoch in seconds
    delay_in_minutes: int = 0
    platform: str = ""

    def remaining_time(self, arriving_threshold = 40) -> str:
        if not self.arrival_time:
            return "-"
    
        now_ts = datetime.now(SPAIN_TZ).timestamp()
        delta_s = self.arrival_time - now_ts

        # Caso 1: Llega muy pronto (< 40s)
        if delta_s <= arriving_threshold:
            return "🔜"

        # Caso 2: Menos de 1 hora → mostrar minutos y segundos
        if delta_s < 60 * 60:
            minutes, seconds = divmod(int(delta_s), 60)

            parts = []
            if minutes:
                parts.append(f"{minutes}min")
            if seconds or not minutes:
                parts.append(f"{seconds}s")

            return " ".join(parts)

        # Convertimos el timestamp de llegada en datetime
        arrival_dt = datetime.fromtimestamp(self.arrival_time)

        # Caso 3: Es hoy pero dentro de más de 1 hora → mostrar hora exacta
        if arrival_dt.date() == datetime.now().date():
            return arrival_dt.strftime("%H:%Mh")

        # Caso 4: No es hoy → mostrar fecha y hora completa
        return arrival_dt.strftime("%d-%m-%Y %H:%Mh")
    
    def scheduled_arrival(self) -> datetime:
        """Devuelve la hora programada de llegada en base al retraso."""
        if not self.arrival_time:
            return None
        return datetime.fromtimestamp(self.arrival_time) - timedelta(minutes=self.delay_in_minutes or 0)
    
def normalize_to_seconds(ts: int) -> int:
    # Si parece milisegundos, lo pasamos a segundos
    return ts // 1000 if ts > 1e11 else ts