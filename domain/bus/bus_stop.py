from dataclasses import dataclass, field
import json
from typing import Optional
from typing import Tuple

import re
from domain.bus.bus_line import BusLine
from providers.helpers.html_helper import HtmlHelper

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
    has_alerts: Optional[bool] = False
    alerts: Optional[list] = field(default_factory=list)

    def __str__(self):
        return f"{self.ORDRE}. {self.NOM_PARADA}"

def create_bus_stop(feature) -> BusStop:
    props = feature["properties"]
    coords = tuple(feature["geometry"]["coordinates"])  # (lon, lat)
    return BusStop(
        ID_RECORREGUT=props.get("ID_RECORREGUT", ""),
        CODI_PARADA=props.get("CODI_PARADA", ""),
        NOM_PARADA=props.get("NOM_PARADA", ""),
        DESC_PARADA=props.get("DESC_PARADA", ""),
        CODI_INTERC=props.get("CODI_INTERC", ""),
        NOM_INTERC=props.get("NOM_INTERC"),
        ADRECA=props.get("ADRECA", ""),
        NOM_POBLACIO=props.get("NOM_POBLACIO", ""),
        NOM_DISTRICTE=props.get("NOM_DISTRICTE", ""),
        NOM_VIA=props.get("NOM_VIA", ""),
        ORDRE=props.get("ORDRE", ""),
        DISTANCIA_PAR_ANTERIOR=props.get("DISTANCIA_PAR_ANTERIOR", ""),
        ES_ORIGEN=props.get("ES_ORIGEN", ""),
        ES_DESTI=props.get("ES_DESTI", ""),
        ES_MAXINODE=props.get("ES_MAXINODE", ""),
        ID_LINIA=props.get("ID_LINIA", ""),
        CODI_LINIA=props.get("CODI_LINIA", ""),
        NOM_LINIA=props.get("NOM_LINIA", ""),
        DESC_LINIA=props.get("DESC_LINIA", ""),
        ORIGEN_SENTIT=props.get("ORIGEN_SENTIT", ""),
        DESTI_SENTIT=props.get("DESTI_SENTIT", ""),
        ID_OPERADOR=props.get("ID_OPERADOR", ""),
        NOM_OPERADOR=props.get("NOM_OPERADOR", ""),
        CODI_FAMILIA=props.get("CODI_FAMILIA", ""),
        NOM_FAMILIA=props.get("NOM_FAMILIA", ""),
        ORDRE_FAMILIA=props.get("ORDRE_FAMILIA", ""),
        ORDRE_LINIA=props.get("ORDRE_LINIA", ""),
        ID_TIPUS_SERVEI=props.get("ID_TIPUS_SERVEI", ""),
        ID_TIPUS_SUB_SERVEI=props.get("ID_TIPUS_SUB_SERVEI", ""),
        NOM_TIPUS_SUB_SERVEI=props.get("NOM_TIPUS_SUB_SERVEI", ""),
        ID_SENTIT=props.get("ID_SENTIT", ""),
        SENTIT=props.get("SENTIT", ""),
        DESC_SENTIT=props.get("DESC_SENTIT", ""),
        ID_TIPUS_RECORREGUT=props.get("ID_TIPUS_RECORREGUT", ""),
        ID_TIPUS_DIA=props.get("ID_TIPUS_DIA", ""),
        CALENDARI_EMULAT=props.get("CALENDARI_EMULAT", ""),
        DATA=props.get("DATA", ""),
        DATA_INICI=props.get("DATA_INICI", ""),
        DATA_FI=props.get("DATA_FI"),
        COLOR_REC=props.get("COLOR_REC", ""),
        PUNTS_PARADA=props.get("PUNTS_PARADA", ""),
        coordinates=coords
    )

def update_bus_stop_with_line_info(bus_stop: BusStop, bus_line: BusLine) -> BusStop:
    if bus_line.has_alerts:
        for alert in bus_line.alerts:
            for entity in alert.affected_entities:
                if entity.line_name == bus_stop.NOM_LINIA and entity.station_code == bus_stop.CODI_PARADA:
                    bus_stop.has_alerts = True
                    if alert.publications not in bus_stop.alerts:
                        bus_stop.alerts = alert.publications

    return bus_stop

def get_alert_by_language(bus_stop: BusStop, language: str):
    raw_alerts = []
    if bus_stop.has_alerts:
        for alert in bus_stop.alerts:
            raw_alerts.append(getattr(alert, f'text{language.capitalize()}'))

    return "\n".join(f"<pre>{alert}</pre>" for alert in set(raw_alerts))


