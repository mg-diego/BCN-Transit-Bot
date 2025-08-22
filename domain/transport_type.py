from enum import Enum

class TransportType(str, Enum):
    BUS = "bus"
    METRO = "metro"
    TRAM = "tram"
    RODALIES = "rodalies"