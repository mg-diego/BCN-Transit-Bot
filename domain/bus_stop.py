from dataclasses import dataclass
from typing import Optional
from typing import Tuple

@dataclass
class BusStop:
    ID_RECORREGUT: int
    CODI_PARADA: int
    NOM_PARADA: str
    DESC_PARADA: str
    CODI_INTERC: int
    NOM_INTERC: Optional[str]
    ADRECA: str
    NOM_POBLACIO: str
    NOM_DISTRICTE: str
    NOM_VIA: str
    ORDRE: int
    DISTANCIA_PAR_ANTERIOR: float
    ES_ORIGEN: int
    ES_DESTI: int
    ES_MAXINODE: int
    ID_LINIA: int
    CODI_LINIA: int
    NOM_LINIA: str
    DESC_LINIA: str
    ORIGEN_SENTIT: str
    DESTI_SENTIT: str
    ID_OPERADOR: int
    NOM_OPERADOR: str
    CODI_FAMILIA: int
    NOM_FAMILIA: str
    ORDRE_FAMILIA: int
    ORDRE_LINIA: int
    ID_TIPUS_SERVEI: int
    ID_TIPUS_SUB_SERVEI: int
    NOM_TIPUS_SUB_SERVEI: str
    ID_SENTIT: int
    SENTIT: str
    DESC_SENTIT: str
    ID_TIPUS_RECORREGUT: int
    ID_TIPUS_DIA: int
    CALENDARI_EMULAT: int
    DATA: str
    DATA_INICI: str
    DATA_FI: Optional[str]
    COLOR_REC: str
    PUNTS_PARADA: int

    coordinates: Tuple[float, float]

    def __str__(self):
        return f"{self.ORDRE}. {self.NOM_PARADA}"

def create_bus_stop(feature) -> BusStop:
    props = feature["properties"]
    coords = tuple(feature["geometry"]["coordinates"])  # (lon, lat)
    return BusStop(
        ID_RECORREGUT=props["ID_RECORREGUT"],
        CODI_PARADA=props["CODI_PARADA"],
        NOM_PARADA=props["NOM_PARADA"],
        DESC_PARADA=props["DESC_PARADA"],
        CODI_INTERC=props["CODI_INTERC"],
        NOM_INTERC=props.get("NOM_INTERC"),
        ADRECA=props["ADRECA"],
        NOM_POBLACIO=props["NOM_POBLACIO"],
        NOM_DISTRICTE=props["NOM_DISTRICTE"],
        NOM_VIA=props["NOM_VIA"],
        ORDRE=props["ORDRE"],
        DISTANCIA_PAR_ANTERIOR=props["DISTANCIA_PAR_ANTERIOR"],
        ES_ORIGEN=props["ES_ORIGEN"],
        ES_DESTI=props["ES_DESTI"],
        ES_MAXINODE=props["ES_MAXINODE"],
        ID_LINIA=props["ID_LINIA"],
        CODI_LINIA=props["CODI_LINIA"],
        NOM_LINIA=props["NOM_LINIA"],
        DESC_LINIA=props["DESC_LINIA"],
        ORIGEN_SENTIT=props["ORIGEN_SENTIT"],
        DESTI_SENTIT=props["DESTI_SENTIT"],
        ID_OPERADOR=props["ID_OPERADOR"],
        NOM_OPERADOR=props["NOM_OPERADOR"],
        CODI_FAMILIA=props["CODI_FAMILIA"],
        NOM_FAMILIA=props["NOM_FAMILIA"],
        ORDRE_FAMILIA=props["ORDRE_FAMILIA"],
        ORDRE_LINIA=props["ORDRE_LINIA"],
        ID_TIPUS_SERVEI=props["ID_TIPUS_SERVEI"],
        ID_TIPUS_SUB_SERVEI=props["ID_TIPUS_SUB_SERVEI"],
        NOM_TIPUS_SUB_SERVEI=props["NOM_TIPUS_SUB_SERVEI"],
        ID_SENTIT=props["ID_SENTIT"],
        SENTIT=props["SENTIT"],
        DESC_SENTIT=props["DESC_SENTIT"],
        ID_TIPUS_RECORREGUT=props["ID_TIPUS_RECORREGUT"],
        ID_TIPUS_DIA=props["ID_TIPUS_DIA"],
        CALENDARI_EMULAT=props["CALENDARI_EMULAT"],
        DATA=props["DATA"],
        DATA_INICI=props["DATA_INICI"],
        DATA_FI=props.get("DATA_FI"),
        COLOR_REC=props["COLOR_REC"],
        PUNTS_PARADA=props["PUNTS_PARADA"],
        coordinates=coords
    )


