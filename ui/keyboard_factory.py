import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from typing import List

from domain.metro import MetroLine, MetroStation, MetroAccess
from domain.bus import BusLine, BusStop
from domain.tram import TramLine, TramStop
from domain.rodalies import RodaliesLine
from domain.transport_type import TransportType
from domain.callbacks import Callbacks

from providers.manager.language_manager import LanguageManager

class KeyboardFactory:

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
            InlineKeyboardButton(self.language_manager.t('main.menu.metro'), callback_data=Callbacks.MENU_METRO_CALLBACK.value),
            InlineKeyboardButton(self.language_manager.t('main.menu.bus'), callback_data=Callbacks.MENU_BUS_CALLBACK.value),
            InlineKeyboardButton(self.language_manager.t('main.menu.tram'), callback_data=Callbacks.MENU_TRAM_CALLBACK.value),
            InlineKeyboardButton(self.language_manager.t('main.menu.rodalies'), callback_data=Callbacks.MENU_RODALIES_CALLBACK.value),
            InlineKeyboardButton(self.language_manager.t('main.menu.favorites'), callback_data=Callbacks.MENU_FAVORITES_CALLBACK.value),
            InlineKeyboardButton(self.language_manager.t('main.menu.language'), callback_data=Callbacks.MENU_LANGUAGE_CALLBACK.value)
        ]
        rows = self._chunk_buttons(keyboard, 2)
        rows.append([InlineKeyboardButton(self.language_manager.t('main.menu.help'),callback_data=Callbacks.MENU_HELP_CALLBACK.value)])
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
            
            [KeyboardButton(self.language_manager.t('main.menu.help'))]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    # === LINES ===
    
    def metro_lines_menu(self, metro_lines: List[MetroLine]) -> InlineKeyboardMarkup:
        sorted_lines = sorted(metro_lines, key=self._custom_sort_key)
        buttons = [
            InlineKeyboardButton(f"{line.NOM_LINIA}  ", callback_data=Callbacks.METRO_LINE.format(line_code=line.CODI_LINIA, line_name=line.ORIGINAL_NOM_LINIA))
            for line in sorted_lines
        ]

        rows = self._chunk_buttons(buttons, 3)
        return InlineKeyboardMarkup(rows)
    
    def bus_category_menu(self, list):
        keyboard = [
            InlineKeyboardButton('🟣 D', callback_data=Callbacks.BUS_CATEGORY_D.value),
            InlineKeyboardButton('🔵 H', callback_data=Callbacks.BUS_CATEGORY_H.value),
            InlineKeyboardButton('🟢 V', callback_data=Callbacks.BUS_CATEGORY_V.value),
            InlineKeyboardButton('🔴 M', callback_data=Callbacks.BUS_CATEGORY_M.value),
            InlineKeyboardButton('⚫ X', callback_data=Callbacks.BUS_CATEGORY_M.value),
            InlineKeyboardButton('🔴 1-60 ', callback_data=Callbacks.BUS_CATEGORY_X.value),
            InlineKeyboardButton('🔴 61-100 ', callback_data=Callbacks.BUS_CATEGORY_1_60.value),
            InlineKeyboardButton('🔴 101-120 ', callback_data=Callbacks.BUS_CATEGORY_101_120.value),
            InlineKeyboardButton('🔴 121-140 ', callback_data=Callbacks.BUS_CATEGORY_121_140.value),
            InlineKeyboardButton('🔴 141-200 ', callback_data=Callbacks.BUS_CATEGORY_141_200.value)
        ]
        rows = self._chunk_buttons(keyboard, 2)
        return InlineKeyboardMarkup(rows)
    
    def bus_lines_menu(self, bus_lines: List[BusLine]):
        buttons = [
            InlineKeyboardButton(f"{line.NOM_LINIA}  ", callback_data=Callbacks.BUS_LINE.format(line_code=line.CODI_LINIA, line_name=line.NOM_LINIA))
            for line in bus_lines
        ]

        rows = self._chunk_buttons(buttons, 3)
        return InlineKeyboardMarkup(rows)
    
    def tram_lines_menu(self, tram_lines: List[TramLine]) -> InlineKeyboardMarkup:
        buttons = [
            InlineKeyboardButton(line.name, callback_data=Callbacks.TRAM_LINE.format(line_code=line.id, line_name=line.original_name))
            for line in tram_lines
        ]
        rows = self._chunk_buttons(buttons, 3)
        return InlineKeyboardMarkup(rows)
    
    def rodalies_lines_menu(self, rodalies_lines: List[RodaliesLine])-> InlineKeyboardMarkup:
        keyboard = []
        for line in rodalies_lines:
            keyboard.append([InlineKeyboardButton(f"{line.emoji_name} - {line.description}  ", callback_data=Callbacks.RODALIES_LINE.format(line_code=line.id))])
        return InlineKeyboardMarkup(keyboard)

    # === STATIONS / STOPS ===

    def metro_stations_menu(self, metro_stations: List[MetroStation], line_id):
        buttons = [
            InlineKeyboardButton(f"{metro_station.ORDRE_ESTACIO}. {metro_station.NOM_ESTACIO}  ", callback_data=Callbacks.METRO_STATION.format(line_code=line_id, station_code=metro_station.CODI_ESTACIO))
            for metro_station in metro_stations
        ]
        rows = self._chunk_buttons(buttons, 2)
        return InlineKeyboardMarkup(rows)
    
    def tram_stops_menu(self, tram_stops: List[TramStop], line_id):
        buttons = [
            InlineKeyboardButton(f"{tram_stop.order}. {tram_stop.name}  ", callback_data=Callbacks.TRAM_STOP.format(line_code=line_id, stop_code=tram_stop.id))
            for tram_stop in tram_stops
        ]
        rows = self._chunk_buttons(buttons, 2)
        return InlineKeyboardMarkup(rows)
    
    def metro_station_access_menu(self, station_accesses: List[MetroAccess]):
        buttons = [
            InlineKeyboardButton(f"{"🛗 " if access.NUM_ASCENSORS > 0 else "🚶‍♂️"}{access.NOM_ACCES}", url=f"https://maps.google.com/?q={access.coordinates[1]},{access.coordinates[0]}")
            for access in station_accesses
        ]
        rows = self._chunk_buttons(buttons, 2)
        return InlineKeyboardMarkup(rows)    
    
    def bus_stops_map_menu(self, encoded):
        keyboard = [
            [KeyboardButton(
                text=self.language_manager.t('keyboard.map'),
                web_app=WebAppInfo(url=f"https://mg-diego.github.io/BCN-Transit-Bot/map.html?data={encoded}"),
            )],
            [KeyboardButton(self.language_manager.t('keyboard.back'))]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    def help_menu(self):
        return InlineKeyboardMarkup([self._back_button(self.BACK_TO_MENU_CALLBACK)])
    
    def update_menu(self, is_favorite: bool, item_type:str, item_id: str, line_id: str, user_id: str):
        if is_favorite:
            fav_button = InlineKeyboardButton(self.language_manager.t('keyboard.favorites.remove'), callback_data=Callbacks.REMOVE_FAVORITE.format(item_type=item_type, line_id=line_id, item_id=item_id))
        else:
            fav_button = InlineKeyboardButton(self.language_manager.t('keyboard.favorites.add'), callback_data=Callbacks.ADD_FAVORITE.format(item_type=item_type, line_id=line_id, item_id=item_id))

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
        TRANSPORT_CONFIG = {
            TransportType.METRO.value: {
                "emoji": "🚇",
                "name_fmt": "{nom_linia} - {name}",
                "callback": lambda item: Callbacks.METRO_STATION.format(
                    line_code=item.get("codi_linia"),
                    station_code=item.get("code")
                ),
            },
            TransportType.BUS.value: {
                "emoji": "🚌",
                "name_fmt": "({code}) {name}",
                "callback": lambda item: Callbacks.BUS_STOP.format(
                    line_code=item.get("codi_linia"),
                    stop_code=item.get("code")
                ),
            },
            TransportType.TRAM.value: {
                "emoji": "🚋",
                "name_fmt": "{nom_linia} - {name}",
                "callback": lambda item: Callbacks.TRAM_STOP.format(
                    line_code=item.get("codi_linia"),
                    stop_code=item.get("code")
                ),
            },
            TransportType.RODALIES.value: {
                "emoji": "🚆",
                "name_fmt": "{nom_linia} - {name}",
                "callback": lambda item: Callbacks.RODALIES_STATION.format(
                    line_code=item.get("codi_linia"),
                    station_code=item.get("code")
                ),
            },
        }

        fav_keyboard = []

        for item in favs:
            config = TRANSPORT_CONFIG.get(item["type"])
            if not config:
                continue

            name = config["name_fmt"].format(
                nom_linia=item.get("nom_linia", "Sin nombre"),
                name=item.get("name", ""),
                code=item.get("code", "")
            )

            fav_keyboard.append([
                InlineKeyboardButton(
                    text=f"{config['emoji']} {name}",
                    callback_data=config["callback"](item)
                )
            ])

        return InlineKeyboardMarkup(fav_keyboard)
    
    def _back_button(self, callback):
        return [InlineKeyboardButton(self.language_manager.t('keyboard.back'), callback_data=callback)]
    
    def restart_search_button(self, callback):
        return InlineKeyboardMarkup([[InlineKeyboardButton(self.language_manager.t('common.reload.btn'), callback_data=callback)]])
    
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
            InlineKeyboardButton(name, callback_data=Callbacks.SET_LANGUAGE.format(language_code=code))
            for code, name in available_languages.items()
        ]
        rows = self._chunk_buttons(buttons, 2)
        return InlineKeyboardMarkup(rows)
    
    def map_or_list_menu(self, type, line_id, line_name):
        """Teclado del menú principal."""
        keyboard = [
            InlineKeyboardButton(self.language_manager.t('common.map'), callback_data=f"{type}_map:{line_id}:{line_name}"),
            InlineKeyboardButton(self.language_manager.t('common.list'), callback_data=f"{type}_list:{line_id}:{line_name}")
        ]
        rows = self._chunk_buttons(keyboard, 2)
        return InlineKeyboardMarkup(rows)

    def reply_keyboard_stations_menu(self, metro_stations: List[MetroStation], bus_stops: List[BusStop]):
        buttons = [
            InlineKeyboardButton(f"🚇 {metro_station.NOM_LINIA} - {metro_station.NOM_ESTACIO}  ", callback_data=Callbacks.METRO_STATION.format(line_code=metro_station.CODI_LINIA, station_code=metro_station.CODI_ESTACIO))
            for metro_station in metro_stations
        ]
        for stop in bus_stops:
            buttons.append(
                InlineKeyboardButton(f"🚌 ({stop.CODI_PARADA}) - {stop.NOM_PARADA}  ", callback_data=Callbacks.BUS_STOP.format(line_code=stop.CODI_LINIA, stop_code=stop.CODI_PARADA))
            )
        rows = self._chunk_buttons(buttons, 1)
        return InlineKeyboardMarkup(rows)
    

    
    