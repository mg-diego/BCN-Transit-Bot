from dataclasses import dataclass
from typing import List

@dataclass
class MetroConnection:
    ID_ESTACIO: int
    CODI_ESTACIO: int
    ID_LINIA_BASE: int
    CODI_LINIA_BASE: int
    ORDRE_BASE: int
    ID_OPERADOR: int
    NOM_OPERADOR: str
    CODI_OPERADOR: str
    CODI_FAMILIA: int
    NOM_FAMILIA: str
    ORDRE_FAMILIA: int
    ID_LINIA: int
    CODI_LINIA: int
    NOM_LINIA: str
    DESC_LINIA: str
    ORIGEN_LINIA: str
    DESTI_LINIA: str
    ORDRE_LINIA: int
    COLOR_LINIA: str
    COLOR_TEXT_LINIA: str
    CODI_ELEMENT_CORRESP: int
    NOM_ELEMENT_CORRESP: str
    DESC_CORRESP: str
    DATA: str

    def __str__(self):
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
        emoji = emojis.get(self.NOM_LINIA, "")
        return f"     {emoji} {self.NOM_LINIA} - {self.DESC_LINIA}"
    

def format_metro_connections(metro_connections: List[MetroConnection]):
    return ("\n".join(str(c) for c in metro_connections))
