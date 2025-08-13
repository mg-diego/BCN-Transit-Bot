from dataclasses import dataclass
from typing import List

@dataclass
class MetroAccess:
    ID_ACCES: int
    CODI_ACCES: int
    NOM_ACCES: str
    CODI_GRUP_ESTACIO: int
    ID_ESTACIO: int
    NOM_ESTACIO: str
    ID_TIPUS_ACCESSIBILITAT: int
    NOM_TIPUS_ACCESSIBILITAT: str
    NUM_ASCENSORS: int
    DATA: str
    coordinates: List[float]

def create_metro_access(feature: dict) -> MetroAccess:
    props = feature["properties"]
    coords = feature["geometry"]["coordinates"]
    return MetroAccess(
        ID_ACCES=props["ID_ACCES"],
        CODI_ACCES=props["CODI_ACCES"],
        NOM_ACCES=props["NOM_ACCES"],
        CODI_GRUP_ESTACIO=props["CODI_GRUP_ESTACIO"],
        ID_ESTACIO=props["ID_ESTACIO"],
        NOM_ESTACIO=props["NOM_ESTACIO"],
        ID_TIPUS_ACCESSIBILITAT=props["ID_TIPUS_ACCESSIBILITAT"],
        NOM_TIPUS_ACCESSIBILITAT=props["NOM_TIPUS_ACCESSIBILITAT"],
        NUM_ASCENSORS=props["NUM_ASCENSORS"],
        DATA=props["DATA"],
        coordinates=coords
    )
