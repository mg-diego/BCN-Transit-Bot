from dataclasses import dataclass
from typing import Tuple

@dataclass
class MetroStation:
    ID_ESTACIO_LINIA: int
    CODI_ESTACIO_LINIA: int
    ID_GRUP_ESTACIO: int
    CODI_GRUP_ESTACIO: int
    ID_ESTACIO: int
    CODI_ESTACIO: int
    NOM_ESTACIO: str
    ORDRE_ESTACIO: int
    ID_LINIA: int
    CODI_LINIA: int
    NOM_LINIA: str
    ORDRE_LINIA: int
    ID_TIPUS_SERVEI: int
    DESC_SERVEI: str
    ORIGEN_SERVEI: str
    DESTI_SERVEI: str
    ID_TIPUS_ACCESSIBILITAT: int
    NOM_TIPUS_ACCESSIBILITAT: str
    ID_TIPUS_ESTAT: int
    NOM_TIPUS_ESTAT: str
    DATA_INAUGURACIO: str
    DATA: str
    COLOR_LINIA: str
    PICTO: str
    PICTO_GRUP: str
    EMOJI_NOM_LINIA: str

    coordinates: Tuple[float, float]

    def __str__(self):
        return f"{self.NOM_ESTACIO} - ID_ESTACIO:{self.ID_ESTACIO} (CODI_ESTACIO:{self.CODI_ESTACIO}) - Coord: {self.coordinates}"

def create_metro_station(feature: dict) -> MetroStation:
    props = feature['properties']
    coords = feature['geometry']['coordinates']
    return MetroStation(
        ID_ESTACIO_LINIA=props['ID_ESTACIO_LINIA'],
        CODI_ESTACIO_LINIA=props['CODI_ESTACIO_LINIA'],
        ID_GRUP_ESTACIO=props['ID_GRUP_ESTACIO'],
        CODI_GRUP_ESTACIO=props['CODI_GRUP_ESTACIO'],
        ID_ESTACIO=props['ID_ESTACIO'],
        CODI_ESTACIO=props['CODI_ESTACIO'],
        NOM_ESTACIO=props['NOM_ESTACIO'],
        ORDRE_ESTACIO=props['ORDRE_ESTACIO'],
        ID_LINIA=props['ID_LINIA'],
        CODI_LINIA=props['CODI_LINIA'],
        NOM_LINIA=props['NOM_LINIA'],
        ORDRE_LINIA=props['ORDRE_LINIA'],
        ID_TIPUS_SERVEI=props['ID_TIPUS_SERVEI'],
        DESC_SERVEI=props['DESC_SERVEI'],
        ORIGEN_SERVEI=props['ORIGEN_SERVEI'],
        DESTI_SERVEI=props['DESTI_SERVEI'],
        ID_TIPUS_ACCESSIBILITAT=props['ID_TIPUS_ACCESSIBILITAT'],
        NOM_TIPUS_ACCESSIBILITAT=props['NOM_TIPUS_ACCESSIBILITAT'],
        ID_TIPUS_ESTAT=props['ID_TIPUS_ESTAT'],
        NOM_TIPUS_ESTAT=props['NOM_TIPUS_ESTAT'],
        DATA_INAUGURACIO=props['DATA_INAUGURACIO'],
        DATA=props['DATA'],
        COLOR_LINIA=props['COLOR_LINIA'],
        PICTO=props['PICTO'],
        PICTO_GRUP=props['PICTO_GRUP'],
        coordinates=(coords[0], coords[1]),
        EMOJI_NOM_LINIA=_set_emoji_at_name(props['NOM_LINIA'])
    )


def _set_emoji_at_name(name):
    emojis = {
        "L1": "🟥",
        "L2": "🟪",
        "L3": "🟩",
        "L4": "🟨",
        "L5": "🟦",
        "L9S": "🟧",
        "L9N": "🟧",
    }
    return f"{emojis.get(name, "")} {name}"

