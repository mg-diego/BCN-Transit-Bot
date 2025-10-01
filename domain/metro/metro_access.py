from dataclasses import dataclass

from domain.common.access import Access

@dataclass
class MetroAccess:

    @staticmethod
    def create_metro_access(feature: dict) -> Access:
        props = feature["properties"]
        coords = feature["geometry"]["coordinates"]
        return Access(
            id=props["ID_ACCES"],
            code=props["CODI_ACCES"],
            name=props["NOM_ACCES"],
            station_group_code=props["CODI_GRUP_ESTACIO"],
            station_id=props["ID_ESTACIO"],
            station_name=props["NOM_ESTACIO"],
            accesibility_type_id=props["ID_TIPUS_ACCESSIBILITAT"],
            accesibility_type=props["NOM_TIPUS_ACCESSIBILITAT"],
            number_of_elevators=props["NUM_ASCENSORS"],
            latitude=coords[1],
            longitude=coords[0]
        )
