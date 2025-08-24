import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from typing import List

from domain.metro import MetroLine, MetroStation, MetroAccess
from domain.bus import BusLine
from domain.tram import TramLine, TramStop
from domain.rodalies import RodaliesLine
from domain.transport_type import TransportType

from providers.manager.language_manager import LanguageManager

class KeyboardFactory:

    MENU_CALLBACK = "menu"
    MENU_METRO_CALLBACK = TransportType.METRO.value
    MENU_BUS_CALLBACK = TransportType.BUS.value
    MENU_TRAM_CALLBACK = TransportType.TRAM.value
    MENU_RODALIES_CALLBACK = TransportType.RODALIES.value
    MENU_FAVORITES_CALLBACK = "favorites"
    MENU_LANGUAGE_CALLBACK = "language"
    MENU_HELP_CALLBACK = "help"

    BACK_TO_MENU_CALLBACK = "back_to_menu"    

    def __init__(self, language_manager: LanguageManager):
        self.language_manager = language_manager
    
    def _chunk_buttons(self, buttons, n=2):
        return [buttons[i:i + n] for i in range(0, len(buttons), n)]
    
    def _custom_sort_key(self, line: str):
        # Buscar número y sufijo opcional
        match = re.match(r"L(\d+)([A-Z]?)", line.ORIGINAL_NOM_LINIA)
        if not match:
            return (999, "")  # Los que no encajan van al final

        num = int(match.group(1))          # Número principal
        suffix = match.group(2) or ""      # Sufijo opcional

        # Queremos que los que no tienen sufijo vayan después de N/S
        suffix_order = {"N": 0, "S": 1, "": 2}
        return (num, suffix_order.get(suffix, 3))

    def create_main_menu(self):
        """Teclado del menú principal."""
        keyboard = [
            InlineKeyboardButton(self.language_manager.t('main.menu.metro'), callback_data=self.MENU_METRO_CALLBACK),
            InlineKeyboardButton(self.language_manager.t('main.menu.bus'), callback_data=self.MENU_BUS_CALLBACK),
            InlineKeyboardButton(self.language_manager.t('main.menu.tram'), callback_data=self.MENU_TRAM_CALLBACK),
            InlineKeyboardButton(self.language_manager.t('main.menu.rodalies'), callback_data=self.MENU_RODALIES_CALLBACK),
            InlineKeyboardButton(self.language_manager.t('main.menu.favorites'), callback_data=self.MENU_FAVORITES_CALLBACK),
            InlineKeyboardButton(self.language_manager.t('main.menu.language'), callback_data=self.MENU_LANGUAGE_CALLBACK)
        ]
        rows = self._chunk_buttons(keyboard, 2)
        rows.append([InlineKeyboardButton(self.language_manager.t('main.menu.help'),callback_data=self.MENU_HELP_CALLBACK)])
        return InlineKeyboardMarkup(rows)
    
    def create_main_menu_replykeyboard(self):
        """Teclado principal como ReplyKeyboard."""
        keyboard = [
            [KeyboardButton(self.language_manager.t('main.menu.metro')),
            KeyboardButton(self.language_manager.t('main.menu.bus'))],
            
            [KeyboardButton(self.language_manager.t('main.menu.tram')),
            KeyboardButton(self.language_manager.t('main.menu.rodalies'))],
            
            [KeyboardButton(self.language_manager.t('main.menu.favorites')),
            KeyboardButton(self.language_manager.t('main.menu.language'))],
            
            [KeyboardButton(self.language_manager.t('main.menu.help'))]  # botón en fila propia
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,    # ajusta tamaño automáticamente
            one_time_keyboard=False  # el teclado permanece visible
        )
    
    # === LINES ===
    
    def metro_lines_menu(self, metro_lines: List[MetroLine]) -> InlineKeyboardMarkup:
        sorted_lines = sorted(metro_lines, key=self._custom_sort_key)
        buttons = [
            InlineKeyboardButton(f"{line.NOM_LINIA}  ", callback_data=f"metro_line:{line.CODI_LINIA}")
            for line in sorted_lines
        ]

        rows = self._chunk_buttons(buttons, 4)
        return InlineKeyboardMarkup(rows)
    
    def bus_lines_paginated_menu(self, bus_lines: List[BusLine], page: int = 0):
        BUTTONS_PER_PAGE = 20
        BUTTONS_PER_ROW = 4

        start = page * BUTTONS_PER_PAGE
        end = start + BUTTONS_PER_PAGE
        current_lines = bus_lines[start:end]

        buttons = [
            InlineKeyboardButton(
                f"{line.NOM_LINIA}  ",
                callback_data=f"bus_line:{line.CODI_LINIA}:{line.NOM_LINIA}"
            )
            for line in current_lines
        ]
        rows = self._chunk_buttons(buttons, BUTTONS_PER_ROW)

        navigation_buttons = []
        if page > 0:
            navigation_buttons.append(
                InlineKeyboardButton(self.language_manager.t('keyboard.previous'), callback_data=f"bus_page:{page - 1}")
            )
        if end < len(bus_lines):
            navigation_buttons.append(
                InlineKeyboardButton(self.language_manager.t('keyboard.next'), callback_data=f"bus_page:{page + 1}")
            )
        if navigation_buttons:
            rows.append(navigation_buttons)

        rows.append(self._back_button(self.BACK_TO_MENU_CALLBACK))
        return InlineKeyboardMarkup(rows)
    
    def tram_lines_menu(self, tram_lines: List[TramLine]) -> InlineKeyboardMarkup:
        buttons = [
            InlineKeyboardButton(line.name, callback_data=f"tram_line:{line.id}:{line.name}")
            for line in tram_lines
        ]
        rows = self._chunk_buttons(buttons, 3)
        return InlineKeyboardMarkup(rows)
    
    def rodalies_lines_menu(self, rodalies_lines: List[RodaliesLine])-> InlineKeyboardMarkup:
        keyboard = []
        for line in rodalies_lines:
            keyboard.append([InlineKeyboardButton(f"{line.emoji_name} - {line.description}  ", callback_data=f"rodalies_line:{line.id}")])
        return InlineKeyboardMarkup(keyboard)

    # === STATIONS / STOPS ===

    def metro_stations_menu(self, metro_stations: List[MetroStation], line_id):
        buttons = [
            InlineKeyboardButton(f"{metro_station.ORDRE_ESTACIO}. {metro_station.NOM_ESTACIO}  ", callback_data=f"metro_station:{line_id}:{metro_station.CODI_ESTACIO}")
            for metro_station in metro_stations
        ]
        rows = self._chunk_buttons(buttons, 2)
        rows.append([InlineKeyboardButton(self.language_manager.t('keyboard.map'), callback_data=f"metro_map:{line_id}")])

        return InlineKeyboardMarkup(rows)
    
    def tram_stops_menu(self, tram_stops: List[TramStop], line_id):
        buttons = [
            InlineKeyboardButton(f"{tram_stop.order}. {tram_stop.name}  ", callback_data=f"tram_stop:{line_id}:{tram_stop.id}")
            for tram_stop in tram_stops
        ]
        rows = self._chunk_buttons(buttons, 2)
        rows.append([InlineKeyboardButton(self.language_manager.t('keyboard.map'), callback_data=f"tram_map:{line_id}")])

        return InlineKeyboardMarkup(rows)
    
    def metro_station_access_menu(self, station_accesses: List[MetroAccess]):
        buttons = [
            InlineKeyboardButton(f"{"🛗 " if access.NUM_ASCENSORS > 0 else "🚶‍♂️"}{access.NOM_ACCES}", url=f"https://maps.google.com/?q={access.coordinates[1]},{access.coordinates[0]}")
            for access in station_accesses
        ]
        rows = self._chunk_buttons(buttons, 2)
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
            if item['type'] == TransportType.METRO.value:
                name = f"{item.get('nom_linia', 'Sin nombre')} - {item.get('name', '')}  "
                fav_keyboard.append([
                    InlineKeyboardButton(f"🚇 {name}", callback_data=f"metro_station:{item.get('codi_linia')}:{item.get('code')}")
                ])
            elif item['type'] == TransportType.BUS.value:
                name = f"({item.get('code', '')})  {item.get('name', '')}  "
                fav_keyboard.append([
                    InlineKeyboardButton(f"🚌 {name}", callback_data=f"bus_stop:{item.get('codi_linia')}:{item.get('code')}")
                ])
            elif item['type'] == TransportType.TRAM.value:
                name = f"{item.get('nom_linia', 'Sin nombre')} - {item.get('name', '')}  "
                fav_keyboard.append([
                    InlineKeyboardButton(f"🚋 {name}", callback_data=f"tram_stop:{item.get('codi_linia')}:{item.get('code')}")
                ])
            elif item['type'] == TransportType.RODALIES.value:
                name = f"{item.get('nom_linia', 'Sin nombre')} - {item.get('name', '')}  "
                fav_keyboard.append([
                    InlineKeyboardButton(f"🚆 {name}", callback_data=f"rodalies_station:{item.get('codi_linia')}:{item.get('code')}")
                ])

        return InlineKeyboardMarkup(fav_keyboard)
    
    def _back_button(self, callback):
        return [InlineKeyboardButton(self.language_manager.t('keyboard.back'), callback_data=callback)]
    
    def _back_reply_button(self):
        """Teclado principal como ReplyKeyboard."""
        keyboard = [
            [KeyboardButton(self.language_manager.t('keyboard.back'))]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,    # ajusta tamaño automáticamente
            one_time_keyboard=False  # el teclado permanece visible
        )
    
    def language_menu(self, available_languages: dict):
        buttons = [
            InlineKeyboardButton(name, callback_data=f"set_language:{code}")
            for code, name in available_languages.items()
        ]
        rows = self._chunk_buttons(buttons, 2)
        rows.append(self._back_button(self.BACK_TO_MENU_CALLBACK))
        return InlineKeyboardMarkup(rows)

    def reply_keyboard_stations_menu(self, metro_stations: List[MetroStation]):
        buttons = [
            InlineKeyboardButton(f"{metro_station.NOM_LINIA} - {metro_station.NOM_ESTACIO}  ", callback_data=f"metro_station:{metro_station.CODI_LINIA}:{metro_station.CODI_ESTACIO}")
            for metro_station in metro_stations
        ]
        rows = self._chunk_buttons(buttons, 1)
        #rows.append(self._back_button(self.BACK_TO_MENU_CALLBACK))
        return InlineKeyboardMarkup(rows)
    