from dataclasses import dataclass
from typing import Optional

@dataclass
class BusLine:
    ID_LINIA: int
    CODI_LINIA: int
    NOM_LINIA: str
    DESC_LINIA: str
    ORIGEN_LINIA: str
    DESTI_LINIA: str
    NUM_PAQUETS: int
    ID_OPERADOR: int
    CODI_OPERADOR: str
    NOM_OPERADOR: str
    ID_TIPUS_TRANSPORT: int
    NOM_TIPUS_TRANSPORT: str
    ID_FAMILIA: int
    CODI_FAMILIA: int
    NOM_FAMILIA: str
    ORDRE_FAMILIA: int
    ORDRE_LINIA: int
    CODI_TIPUS_CALENDARI: str
    NOM_TIPUS_CALENDARI: str
    DATA: str  # puedes usar datetime si lo vas a parsear
    COLOR_LINIA: str
    COLOR_AUX_LINIA: str
    COLOR_TEXT_LINIA: str
    ORIGINAL_NOM_LINIA: Optional[str] = None

    def __post_init__(self):
        emojis = {
            "H": "🟦",
            "D": "🟪",
            "V": "🟩",
            "M": "🔴",
            "X": "🟨"
        }

        self.ORIGINAL_NOM_LINIA = self.NOM_LINIA

        for letra in self.NOM_LINIA:
            if letra in emojis:
                self.NOM_LINIA = f"{emojis[letra]} {self.NOM_LINIA}"
                break
        else:
            if self.NOM_LINIA.isdigit():
                self.NOM_LINIA = f"🔴 {self.NOM_LINIA}"

    def __str__(self):
        return (
            f"🚌 Línia {self.NOM_LINIA} ({self.NOM_TIPUS_TRANSPORT})\n"
            f"🔁 Ruta: {self.ORIGEN_LINIA} ➝ {self.DESTI_LINIA}\n"
            f"🏷️ Descripció: {self.DESC_LINIA}\n"
            f"🎨 Colors: #{self.COLOR_LINIA}, #{self.COLOR_TEXT_LINIA}\n"
            f"🚩 Operador: {self.NOM_OPERADOR} ({self.CODI_OPERADOR})\n"
            f"📅 Calendari: {self.NOM_TIPUS_CALENDARI}\n"
            f"📁 Família: {self.NOM_FAMILIA}\n"
            f"📆 Data: {self.DATA}"
        )
