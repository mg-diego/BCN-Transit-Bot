from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List

from domain.metro_line import MetroLine
from domain.metro_station import MetroStation
from domain.metro_access import MetroAccess
from domain.bus_line import BusLine

class KeyboardFactory:

    MENU_CALLBACK = "menu"
    MENU_METRO_CALLBACK = "metro"
    MENU_BUS_CALLBACK = "bus"
    MENU_FAVORITES_CALLLBACK = "favorites"
    MENU_FAVORITES_CALLBACK = "help"

    
    def _chunk_buttons(self, buttons, n=2):
        return [buttons[i:i + n] for i in range(0, len(buttons), n)]

    def create_main_menu(self):
        """Teclado del menú principal."""
        keyboard = [
            [InlineKeyboardButton("🚇 Metro", callback_data=self.MENU_METRO_CALLBACK)],
            [InlineKeyboardButton("🚌 Bus", callback_data=self.MENU_BUS_CALLBACK)],
            [InlineKeyboardButton("⭐ Favoritos", callback_data=self.MENU_FAVORITES_CALLLBACK)],
            [InlineKeyboardButton("ℹ️ Ayuda", callback_data=self.MENU_FAVORITES_CALLBACK)]
        ]
        return InlineKeyboardMarkup(keyboard)    
    
    def metro_lines_menu(self, metro_lines: List[MetroLine]) -> InlineKeyboardMarkup:
        keyboard = []
        for line in metro_lines:
            keyboard.append([InlineKeyboardButton(f"{line.NOM_LINIA} - {line.DESC_LINIA}", callback_data=f"metro_line:{line.CODI_LINIA}")])
        keyboard.append(self._back_button(self.MENU_CALLBACK))
        return InlineKeyboardMarkup(keyboard)
    
    def metro_stations_menu(self, metro_stations: List[MetroStation], line_id):
        buttons = [
            InlineKeyboardButton(f"{metro_station.ORDRE_ESTACIO}. {metro_station.NOM_ESTACIO}", callback_data=f"metro_station:{line_id}:{metro_station.CODI_ESTACIO}")
            for metro_station in metro_stations
        ]
        rows = self._chunk_buttons(buttons, 2)
        rows.append(self._back_button(self.MENU_METRO_CALLBACK))
        return InlineKeyboardMarkup(rows)
    
    def metro_station_access_menu(self, station_accesses: List[MetroAccess]):
        buttons = [
            InlineKeyboardButton(f"{"🛗 " if access.NUM_ASCENSORS > 0 else "🚶‍♂️"}{access.NOM_ACCES}", url=f"https://maps.google.com/?q={access.coordinates[1]},{access.coordinates[0]}")
            for access in station_accesses
        ]
        rows = self._chunk_buttons(buttons, 2)
        return InlineKeyboardMarkup(rows)
    
    def help_menu(self):
        return InlineKeyboardMarkup([self._back_button(self.MENU_CALLBACK)])
    
    def close_updates_menu(self, user_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cerrar", callback_data=f"close_updates:{user_id}")]
        ])
    
    def _back_button(self, callback):
        return [InlineKeyboardButton("🔙 Volver", callback_data=callback)]
    


















    def bus_lines_menu(self, bus_lines: List[BusLine]) -> InlineKeyboardMarkup:
        buttons = [
            InlineKeyboardButton(f"{line.NOM_LINIA}", callback_data=f"bus_line:{line.CODI_LINIA}:{line.NOM_LINIA}")
            for line in bus_lines
        ]
        rows = self.chunk_buttons(buttons, 5)

        buttons.append([InlineKeyboardButton("🔙 Volver", callback_data="menu_main")])
        return InlineKeyboardMarkup(rows)

    def favorites_menu(self, is_favorite: bool, item_type:str, item_id: str):
        if is_favorite:
            fav_button = InlineKeyboardButton("💔 Quitar de Favoritos", callback_data=f"remove_fav:{item_type}:{item_id}")
        else:
            fav_button = InlineKeyboardButton("♥️ Añadir a Favoritos", callback_data=f"add_fav:{item_type}:{item_id}")

        keyboard = InlineKeyboardMarkup([
            [
                fav_button,
                InlineKeyboardButton("❌ Cerrar", callback_data="close_station_info")
            ]
        ])
        return keyboard
    
    def chunk_buttons(buttons, n=2):
        return [buttons[i:i + n] for i in range(0, len(buttons), n)]