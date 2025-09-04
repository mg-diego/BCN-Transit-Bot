from enum import Enum

class TransportType(Enum):
    BUS = (7, "bus")
    METRO = (2, "metro")
    TRAM = (4, "tram")
    RODALIES = (10, "rodalies")
    BICING = (999, "bicing")
    FGC = (1, "fgc")

    def __new__(cls, id_, value):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.id = id_
        return obj