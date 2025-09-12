from dataclasses import dataclass

from domain.bus.bus_line import BusLine
from domain.common.station import Station

@dataclass
class BusStop(Station):
    DESTI_SENTIT: str

    @staticmethod
    def create_bus_stop(feature):
        props = feature["properties"]
        coords = tuple(feature["geometry"]["coordinates"])  # (lon, lat)

        return BusStop(
            id=props.get("ID_RECORREGUT", ""),
            code=props.get("CODI_PARADA", ""),
            name=props.get("NOM_PARADA", ""),
            description=props.get("DESC_PARADA", ""),
            order=props.get("ORDRE", ""),
            line_id=props.get("ID_LINIA", ""),
            line_code=props.get("CODI_LINIA", ""),
            line_name=props.get("NOM_LINIA", ""),
            DESTI_SENTIT=props.get("DESTI_SENTIT", ""),
            line_color=props.get("COLOR_REC", ""),
            latitude=coords[1],
            longitude=coords[0]
        )

    @staticmethod
    def update_bus_stop_with_line_info(bus_stop: Station, bus_line: BusLine):
        if bus_line.has_alerts:
            for alert in bus_line.alerts:                
                for entity in alert.affected_entities:
                    if entity.line_name == bus_stop.line_name and entity.station_code == bus_stop.code:
                        bus_stop.has_alerts = True
                        if alert.publications not in bus_stop.alerts:
                            bus_stop.alerts = alert.publications

        return bus_stop


