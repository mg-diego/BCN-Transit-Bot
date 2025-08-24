from dataclasses import dataclass
from typing import Optional

@dataclass
class MetroLine:
    ID_LINIA: int
    CODI_LINIA: int
    NOM_LINIA: str
    DESC_LINIA: str
    ORIGEN_LINIA: str
    DESTI_LINIA: str
    NUM_PAQUETS: int
    ID_OPERADOR: int
    NOM_OPERADOR: str
    NOM_TIPUS_TRANSPORT: str
    CODI_FAMILIA: int
    NOM_FAMILIA: str
    ORDRE_FAMILIA: int
    ORDRE_LINIA: int
    CODI_TIPUS_CALENDARI: str
    NOM_TIPUS_CALENDARI: str
    DATA: str
    COLOR_LINIA: str
    COLOR_AUX_LINIA: str
    COLOR_TEXT_LINIA: str
    ORIGINAL_NOM_LINIA: Optional[str] = None

    def __post_init__(self):
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
        self.ORIGINAL_NOM_LINIA = self.NOM_LINIA
        self.NOM_LINIA = f"{emoji} {self.NOM_LINIA}"

    def __str__(self):
        return f"{self.NOM_LINIA} - {self.DESC_LINIA} ({self.ORIGEN_LINIA} ↔ {self.DESTI_LINIA})"
