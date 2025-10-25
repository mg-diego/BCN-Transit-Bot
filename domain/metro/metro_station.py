from dataclasses import dataclass
from domain.metro import MetroLine
from domain.transport_type import TransportType
from domain.common.station import Station

@dataclass
class MetroStation(Station):
    CODI_GRUP_ESTACIO: int
    ORIGEN_SERVEI: str
    DESTI_SERVEI: str

    @staticmethod
    def create_metro_station(feature: dict):
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        return MetroStation(
            CODI_GRUP_ESTACIO=props.get('CODI_GRUP_ESTACIO',''),
            id=props.get('ID_ESTACIO', ''),
            code=props.get('CODI_ESTACIO',''),
            name=props.get('NOM_ESTACIO', ''),
            order=props.get('ORDRE_ESTACIO', ''),
            line_id=props.get('ID_LINIA', ''),
            line_code=props.get('CODI_LINIA', ''),
            line_name=props.get('NOM_LINIA', ''),
            line_color=props.get('COLOR_LINIA', ''),
            line_name_with_emoji=_set_emoji_at_name(props.get('NOM_LINIA', '')),
            description=props.get('DESC_SERVEI', ''),
            ORIGEN_SERVEI=props.get('ORIGEN_SERVEI', ''),
            DESTI_SERVEI=props.get('DESTI_SERVEI', ''),
            latitude=coords[1],
            longitude=coords[0],
            transport_type=TransportType.METRO
        )

    @staticmethod
    def update_metro_station_with_line_info(metro_station: Station, metro_line: MetroLine) -> Station:
        metro_station.line_description = metro_line.description
        metro_station.line_id = metro_line.id
        metro_station.line_code = metro_line.code
        metro_station.line_name = metro_line.name
        metro_station.line_name_with_emoji = _set_emoji_at_name(metro_station.line_name)
        if metro_line.has_alerts:
            for alert in metro_line.alerts:
                for entity in alert.affected_entities:
                    if entity.station_code == str(metro_station.code):
                        metro_station.has_alerts = True
                        metro_station.alerts = alert.publications

        return metro_station

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

