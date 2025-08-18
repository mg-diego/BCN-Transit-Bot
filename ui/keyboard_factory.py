from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
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
    
    def bus_lines_menu(self, bus_lines: List[BusLine])  -> InlineKeyboardMarkup:
        buttons = [
            InlineKeyboardButton(f"{line.NOM_LINIA}", callback_data=f"bus_line:{line.CODI_LINIA}:{line.NOM_LINIA}")
            for line in bus_lines
        ]
        rows = self._chunk_buttons(buttons, 5)
        buttons.append(self._back_button(self.MENU_CALLBACK))
        return InlineKeyboardMarkup(rows)
    
    def bus_stops_map_menu(self, encoded):
        return ReplyKeyboardMarkup.from_button(
                KeyboardButton(
                    text="🗺️ Abrir mapa y seleccionar parada",
                    web_app=WebAppInfo(url=f"https://mg-diego.github.io/BCN-Transit-Bot/map.html?data={encoded}"),
                )
        )
    
    def help_menu(self):
        return InlineKeyboardMarkup([self._back_button(self.MENU_CALLBACK)])
    
    def update_menu(self, is_favorite: bool, item_type:str, item_id: str, line_id: str, user_id: str):
        if is_favorite:
            fav_button = InlineKeyboardButton("💔 Quitar de Favoritos", callback_data=f"remove_fav:{item_type}:{line_id}:{item_id}")
        else:
            fav_button = InlineKeyboardButton("♥️ Añadir a Favoritos", callback_data=f"add_fav:{item_type}:{line_id}:{item_id}")

        keyboard = InlineKeyboardMarkup([
            [
                fav_button,
                InlineKeyboardButton("❌ Cerrar", callback_data=f"close_updates:{user_id}")
            ]
        ])
        return keyboard
    
    def error_menu(self, user_id):
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ Cerrar", callback_data=f"close_updates:{user_id}")
            ]
        ])
        return keyboard
    
    def favorites_menu(self, favs):
        fav_keyboard = []
        # Metro favorites
        for item in favs:
            if item['type'] == "metro":
                name = f"{item.get('nom_linia', 'Sin nombre')} - {item.get('name', '')}"
                fav_keyboard.append([
                    InlineKeyboardButton(f"🚇 {name}", callback_data=f"metro_station:{item.get('codi_linia')}:{item.get('code')}")
                ])
            elif item['type'] == "bus":
                name = f"({item.get('code', '')})  {item.get('name', '')}"
                fav_keyboard.append([
                    InlineKeyboardButton(f"🚌 {name}", callback_data=f"bus_stop:{item.get('codi_linia')}:{item.get('code')}")
                ])

        # Close button
        fav_keyboard.append(self._back_button(self.MENU_CALLBACK))
        return InlineKeyboardMarkup(fav_keyboard)
    
    def _back_button(self, callback):
        return [InlineKeyboardButton("🔙 Volver", callback_data=callback)]
    