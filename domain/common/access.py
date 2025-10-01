from dataclasses import dataclass

@dataclass
class Access:
    id: int
    code: int
    name: str
    station_group_code: int
    station_id: int
    station_name: str
    accesibility_type_id: int
    accesibility_type: str
    number_of_elevators: int
    latitude: float
    longitude: float
