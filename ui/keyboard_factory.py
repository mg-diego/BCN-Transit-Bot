from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from typing import List

from domain.metro.metro_line import MetroLine
from domain.metro.metro_station import MetroStation
from domain.metro.metro_access import MetroAccess
from domain.bus.bus_line import BusLine
from domain.tram.tram_line import TramLine
from domain.tram.tram_stop import TramStop

class KeyboardFactory:

    MENU_CALLBACK = "menu"
    MENU_METRO_CALLBACK = "metro"
    MENU_BUS_CALLBACK = "bus"
    MENU_TRAM_CALLBACK = "tram"
    MENU_FAVORITES_CALLBACK = "favorites"
    MENU_LANGUAGE_CALLBACK = "language"
    MENU_HELP_CALLBACK = "help"

    BACK_TO_MENU_CALLBACK = "back_to_menu"

    def __init__(self, language_manager):
        self.language_manager = language_manager
    
    def _chunk_buttons(self, buttons, n=2):
        return [buttons[i:i + n] for i in range(0, len(buttons), n)]

    def create_main_menu(self):
        """Teclado del menú principal."""
        keyboard = [
            InlineKeyboardButton(self.language_manager.t('main.menu.metro'), callback_data=self.MENU_METRO_CALLBACK),
            InlineKeyboardButton(self.language_manager.t('main.menu.bus'), callback_data=self.MENU_BUS_CALLBACK),
            InlineKeyboardButton(self.language_manager.t('main.menu.tram'), callback_data=self.MENU_TRAM_CALLBACK),
            InlineKeyboardButton(self.language_manager.t('main.menu.favorites'), callback_data=self.MENU_FAVORITES_CALLBACK),
            InlineKeyboardButton(self.language_manager.t('main.menu.language'), callback_data=self.MENU_LANGUAGE_CALLBACK),
            InlineKeyboardButton(self.language_manager.t('main.menu.help'),callback_data=self.MENU_HELP_CALLBACK)
        ]
        rows = self._chunk_buttons(keyboard, 2)
        #rows.append([InlineKeyboardButton(self.language_manager.t('main.menu.help'),callback_data=self.MENU_HELP_CALLBACK)])
        return InlineKeyboardMarkup(rows)
    
    def metro_lines_menu(self, metro_lines: List[MetroLine]) -> InlineKeyboardMarkup:
        keyboard = []
        for line in metro_lines:
            keyboard.append([InlineKeyboardButton(f"{line.NOM_LINIA} - {line.DESC_LINIA}", callback_data=f"metro_line:{line.CODI_LINIA}")])
        keyboard.append(self._back_button(self.BACK_TO_MENU_CALLBACK))
        return InlineKeyboardMarkup(keyboard)
    
    def tram_lines_menu(self, tram_lines: List[TramLine]) -> InlineKeyboardMarkup:
        buttons = [
            InlineKeyboardButton(line.name, callback_data=f"tram_line:{line.id}:{line.name}")
            for line in tram_lines
        ]
        rows = self._chunk_buttons(buttons, 2)
        rows.append(self._back_button(self.BACK_TO_MENU_CALLBACK))
        return InlineKeyboardMarkup(rows)
    
    def metro_stations_menu(self, metro_stations: List[MetroStation], line_id):
        buttons = [
            InlineKeyboardButton(f"{metro_station.ORDRE_ESTACIO}. {metro_station.NOM_ESTACIO}", callback_data=f"metro_station:{line_id}:{metro_station.CODI_ESTACIO}")
            for metro_station in metro_stations
        ]
        rows = self._chunk_buttons(buttons, 2)
        rows.append([InlineKeyboardButton(self.language_manager.t('keyboard.map'), callback_data=f"metro_map:{line_id}")])
        rows.append(self._back_button(self.BACK_TO_MENU_CALLBACK))
        return InlineKeyboardMarkup(rows)
    
    def tram_stops_menu(self, tram_stops: List[TramStop], line_id):
        buttons = [
            InlineKeyboardButton(f"{tram_stop.order}. {tram_stop.name}", callback_data=f"tram_stop:{line_id}:{tram_stop.id}")
            for tram_stop in tram_stops
        ]
        rows = self._chunk_buttons(buttons, 2)
        rows.append(self._back_button(self.BACK_TO_MENU_CALLBACK))
        return InlineKeyboardMarkup(rows)
    
    def metro_station_access_menu(self, station_accesses: List[MetroAccess]):
        buttons = [
            InlineKeyboardButton(f"{"🛗 " if access.NUM_ASCENSORS > 0 else "🚶‍♂️"}{access.NOM_ACCES}", url=f"https://maps.google.com/?q={access.coordinates[1]},{access.coordinates[0]}")
            for access in station_accesses
        ]
        rows = self._chunk_buttons(buttons, 2)
        return InlineKeyboardMarkup(rows)
    
    def bus_lines_menu(self, bus_lines: List[BusLine]):
        buttons = [
            InlineKeyboardButton(f"{line.NOM_LINIA}", callback_data=f"bus_line:{line.CODI_LINIA}:{line.NOM_LINIA}")
            for line in bus_lines
        ]
        rows = self._chunk_buttons(buttons, 5)
        rows.append(self._back_button(self.BACK_TO_MENU_CALLBACK))
        return InlineKeyboardMarkup(rows)
    
    def bus_stops_map_menu(self, encoded):
        return ReplyKeyboardMarkup.from_button(
                KeyboardButton(
                    text=self.language_manager.t('keyboard.map'),
                    web_app=WebAppInfo(url=f"https://mg-diego.github.io/BCN-Transit-Bot/map.html?data={encoded}"),
                )
        )
    
    def help_menu(self):
        return InlineKeyboardMarkup([self._back_button(self.BACK_TO_MENU_CALLBACK)])
    
    def update_menu(self, is_favorite: bool, item_type:str, item_id: str, line_id: str, user_id: str):
        if is_favorite:
            fav_button = InlineKeyboardButton(self.language_manager.t('keyboard.favorites.remove'), callback_data=f"remove_fav:{item_type}:{line_id}:{item_id}")
        else:
            fav_button = InlineKeyboardButton(self.language_manager.t('keyboard.favorites.add'), callback_data=f"add_fav:{item_type}:{line_id}:{item_id}")

        keyboard = InlineKeyboardMarkup([
            [
                fav_button,
                self._close_button(user_id)
            ]
        ])
        return keyboard
    
    def error_menu(self, user_id):
        keyboard = InlineKeyboardMarkup([
            [
                self._close_button(user_id)
            ]
        ])
        return keyboard
    
    def _close_button(self, user_id: str):
        """Devuelve el botón de cerrar menú."""
        return InlineKeyboardButton(
            self.language_manager.t('keyboard.close'),
            callback_data=f"close_updates:{user_id}"
    )
    
    def favorites_menu(self, favs):
        fav_keyboard = []

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

        fav_keyboard.append(self._back_button(self.BACK_TO_MENU_CALLBACK))
        return InlineKeyboardMarkup(fav_keyboard)
    
    def _back_button(self, callback):
        return [InlineKeyboardButton(self.language_manager.t('keyboard.back'), callback_data=callback)]
    
    def language_menu(self, available_languages: dict):
        buttons = [
            InlineKeyboardButton(name, callback_data=f"set_language:{code}")
            for code, name in available_languages.items()
        ]
        rows = self._chunk_buttons(buttons, 2)
        rows.append(self._back_button(self.BACK_TO_MENU_CALLBACK))
        return InlineKeyboardMarkup(rows)
    