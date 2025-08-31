from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import json

from domain.metro import MetroLine, MetroConnection
from providers.helpers.html_helper import HtmlHelper

@dataclass
class MetroStation:
    CODI_GRUP_ESTACIO: int
    ID_ESTACIO: int
    CODI_ESTACIO: int
    NOM_ESTACIO: str
    ORDRE_ESTACIO: int
    ID_LINIA: int
    CODI_LINIA: int
    NOM_LINIA: str
    ORDRE_LINIA: int
    DESC_SERVEI: str
    ORIGEN_SERVEI: str
    DESTI_SERVEI: str
    DATA: str
    COLOR_LINIA: str
    PICTO: str
    PICTO_GRUP: str
    EMOJI_NOM_LINIA: str
    coordinates: Tuple[float, float]
    has_alerts: Optional[bool] = False
    alerts: Optional[list] = field(default_factory=lambda: defaultdict(list))    
    connections: Optional[list[MetroConnection]] = field(default_factory=lambda: defaultdict(list))

def create_metro_station(feature: dict) -> MetroStation:
    props = feature['properties']
    coords = feature['geometry']['coordinates']
    return MetroStation(
        CODI_GRUP_ESTACIO=props.get('CODI_GRUP_ESTACIO',''),
        ID_ESTACIO=props.get('ID_ESTACIO', ''),
        CODI_ESTACIO=props.get('CODI_ESTACIO',''),
        NOM_ESTACIO=props.get('NOM_ESTACIO', ''),
        ORDRE_ESTACIO=props.get('ORDRE_ESTACIO', ''),
        ID_LINIA=props.get('ID_LINIA', ''),
        CODI_LINIA=props.get('CODI_LINIA', ''),
        NOM_LINIA=props.get('NOM_LINIA', ''),
        ORDRE_LINIA=props.get('ORDRE_LINIA', ''),
        COLOR_LINIA=props.get('COLOR_LINIA', ''),
        EMOJI_NOM_LINIA=_set_emoji_at_name(props.get('NOM_LINIA', '')),
        DESC_SERVEI=props.get('DESC_SERVEI', ''),
        ORIGEN_SERVEI=props.get('ORIGEN_SERVEI', ''),
        DESTI_SERVEI=props.get('DESTI_SERVEI', ''),
        DATA=props.get('DATA', ''),
        PICTO=props.get('PICTO', ''),
        PICTO_GRUP=props.get('PICTO_GRUP', ''),
        coordinates=(coords[0], coords[1]),
    )

def update_metro_station_with_line_info(metro_station: MetroStation, metro_line: MetroLine) -> MetroStation:
    metro_station.ID_LINIA = metro_line.ID_LINIA
    metro_station.CODI_LINIA = metro_line.CODI_LINIA
    metro_station.NOM_LINIA = metro_line.ORIGINAL_NOM_LINIA
    metro_station.ORDRE_LINIA = metro_line.ORDRE_LINIA
    metro_station.EMOJI_NOM_LINIA = _set_emoji_at_name(metro_station.NOM_LINIA)
    if metro_line.has_alerts:
        line_alerts = json.loads(metro_line.raw_alerts)
        for alert in line_alerts:
            for entity in alert.get('entities', []):
                if entity.get('station_code') == str(metro_station.CODI_ESTACIO):
                    metro_station.has_alerts = True
                    metro_station.alerts = alert.get('publications', [])

    return metro_station

def update_metro_station_with_connections(metro_station: MetroStation, connections: List[MetroConnection]) -> MetroStation:
    metro_station.connections = sorted(connections, key=lambda c: HtmlHelper.custom_sort_key(c.NOM_LINIA))
    return metro_station
 
def get_alert_by_language(metro_station: MetroStation, language: str):
    raw_alerts = []
    if metro_station.has_alerts:
        text_key = f'text{language.capitalize()}'
        for alert in metro_station.alerts:
            raw_alerts.append(f"{alert.get(text_key)}")

    return "\n".join(f"<pre>{alert}</pre>" for alert in raw_alerts)

def _set_emoji_at_name(name):
    emojis = {
        "L1": "🟥",
        "L2": "🟪",
        "L3": "🟩",
        "L4": "🟨",
        "L5": "🟦",
        "L9N": "🟧",
        "L9S": "🟧",
        "L10N": "🟦",
        "L10S": "🟦",
        "L11": "🟩",
    }
    return f"{emojis.get(name, "")} {name}"

