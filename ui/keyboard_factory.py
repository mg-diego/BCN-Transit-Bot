import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from typing import List

from domain.metro import MetroLine, MetroStation, MetroAccess
from domain.bus import BusLine, BusStop
from domain.tram import TramLine, TramStation
from domain.rodalies import RodaliesLine
from domain.transport_type import TransportType
from domain.fgc import FgcLine, FgcStation
from domain.callbacks import Callbacks

from providers.helpers.utils import Utils
from providers.manager import LanguageManager
from providers.helpers import DistanceHelper, GoogleMapsHelper

class KeyboardFactory:

    BACK_TO_MENU_CALLBACK = "back_to_menu"

    def location_keyboard(self):
        keyboard = [[KeyboardButton(self.language_manager.t('results.location.btn'), request_location=True)], [KeyboardButton(self.language_manager.t('keyboard.back'))]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    def __init__(self, language_manager: LanguageManager):
        self.language_manager = language_manager
    
    def _chunk_buttons(self, buttons, n=2):
        return [buttons[i:i + n] for i in range(0, len(buttons), n)]
    
    def _custom_sort_key(self, line: str):
        # Buscar número y sufijo opcional
        match = re.match(r"L(\d+)([A-Z]?)", line.name)
        if not match:
            return (999, "")  # Los que no encajan van al final

        num = int(match.group(1))          # Número principal
        suffix = match.group(2) or ""      # Sufijo opcional

        # Queremos que los que no tienen sufijo vayan después de N/S
        suffix_order = {"N": 0, "S": 1, "": 2}
        return (num, suffix_order.get(suffix, 3))
    
    def create_main_menu_replykeyboard(self):
        """Teclado principal como ReplyKeyboard."""
        keyboard = [
            [KeyboardButton(f"{TransportType.METRO.emoji} {self.language_manager.t('main.menu.metro')}"),
            KeyboardButton(f"{TransportType.BUS.emoji} {self.language_manager.t('main.menu.bus')}"),
            KeyboardButton(f"{TransportType.TRAM.emoji} {self.language_manager.t('main.menu.tram')}")],
            
            [KeyboardButton(f"{TransportType.BICING.emoji} {self.language_manager.t('main.menu.bicing')}"),
            KeyboardButton(f"{TransportType.RODALIES.emoji} {self.language_manager.t('main.menu.rodalies')}"),
            KeyboardButton(f"{TransportType.FGC.emoji} {self.language_manager.t('main.menu.fgc')}")],
            
            [KeyboardButton(self.language_manager.t('main.menu.favorites')),
            KeyboardButton(self.language_manager.t('main.menu.near')),
            KeyboardButton(self.language_manager.t('main.menu.settings'))]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    def settings_replykeyboard(self):
        keyboard = [
            [KeyboardButton(self.language_manager.t('settings.notifications')),
            KeyboardButton(self.language_manager.t('settings.language'))],

            [KeyboardButton(self.language_manager.t('settings.help'))],

            [KeyboardButton(self.language_manager.t('keyboard.back'))]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    # === LINES ===
    
    def metro_lines_menu(self, metro_lines: List[MetroLine]) -> InlineKeyboardMarkup:
        sorted_lines = sorted(metro_lines, key=Utils.sort_lines)
        buttons = [
            InlineKeyboardButton(f"{line.name_with_emoji} {'⚠️' if line.has_alerts else ''}  ", callback_data=Callbacks.METRO_LINE.format(line_code=line.code, line_name=line.name))
            for line in sorted_lines
        ]

        rows = self._chunk_buttons(buttons, 3)
        return InlineKeyboardMarkup(rows)
    
    def bus_category_menu(self, lines): #Do not delete lines, it's used for compliance at handler base
        keyboard = [
            InlineKeyboardButton('🟣 D', callback_data=Callbacks.BUS_CATEGORY_D.value),
            InlineKeyboardButton('🔵 H', callback_data=Callbacks.BUS_CATEGORY_H.value),
            InlineKeyboardButton('🟢 V', callback_data=Callbacks.BUS_CATEGORY_V.value),
            InlineKeyboardButton('🔴 M', callback_data=Callbacks.BUS_CATEGORY_M.value),
            InlineKeyboardButton('⚫ X', callback_data=Callbacks.BUS_CATEGORY_X.value),
            InlineKeyboardButton('🔴 1-60 ', callback_data=Callbacks.BUS_CATEGORY_1_60.value),
            InlineKeyboardButton('🔴 61-100 ', callback_data=Callbacks.BUS_CATEGORY_61_100.value),
            InlineKeyboardButton('🔴 101-120 ', callback_data=Callbacks.BUS_CATEGORY_101_120.value),
            InlineKeyboardButton('🔴 121-140 ', callback_data=Callbacks.BUS_CATEGORY_121_140.value),
            InlineKeyboardButton('🔴 141-200 ', callback_data=Callbacks.BUS_CATEGORY_141_200.value)
        ]
        rows = self._chunk_buttons(keyboard, 2)
        return InlineKeyboardMarkup(rows)
    
    def bus_lines_menu(self, bus_lines: List[BusLine]):
        buttons = [
            InlineKeyboardButton(f"{line.NOM_LINIA} {'⚠️' if line.has_alerts else ''}  ", callback_data=Callbacks.BUS_LINE.format(line_code=line.CODI_LINIA, line_name=line.NOM_LINIA))
            for line in bus_lines
        ]

        rows = self._chunk_buttons(buttons, 3)
        return InlineKeyboardMarkup(rows)
    
    def tram_lines_menu(self, tram_lines: List[TramLine]) -> InlineKeyboardMarkup:
        buttons = [
            InlineKeyboardButton(f"{line.name_with_emoji} {'⚠️' if line.has_alerts else ''}  ", callback_data=Callbacks.TRAM_LINE.format(line_code=line.id, line_name=line.name))
            for line in tram_lines
        ]
        rows = self._chunk_buttons(buttons, 3)
        return InlineKeyboardMarkup(rows)
    
    def rodalies_lines_menu(self, rodalies_lines: List[RodaliesLine])-> InlineKeyboardMarkup:
        buttons = [
            InlineKeyboardButton(f" {'⚠️ ' if line.has_alerts else ''}{line.emoji_name}  ", callback_data=Callbacks.RODALIES_LINE.format(line_code=line.id))
            for line in rodalies_lines
        ]
        rows = self._chunk_buttons(buttons, 3)
        return InlineKeyboardMarkup(rows)
    
    def fgc_lines_menu(self, fgc_lines: List[FgcLine])-> InlineKeyboardMarkup:
        buttons = [
            InlineKeyboardButton(f" {'⚠️ ' if line.has_alerts else ''}{line.name_with_emoji}  ", callback_data=Callbacks.FGC_LINE.format(line_code=line.id, line_name=line.name))
            for line in fgc_lines
        ]
        rows = self._chunk_buttons(buttons, 4)
        return InlineKeyboardMarkup(rows)

    # === STATIONS / STOPS ===

    def metro_stations_menu(self, metro_stations: List[MetroStation], line_id):
        buttons = [
            InlineKeyboardButton(f"{metro_station.order}. {metro_station.name} {'⚠️' if metro_station.has_alerts else ''}  ", callback_data=Callbacks.METRO_STATION.format(line_code=line_id, station_code=metro_station.code))
            for metro_station in metro_stations
        ]
        rows = self._chunk_buttons(buttons, 2)
        return InlineKeyboardMarkup(rows)
    
    def tram_stops_menu(self, tram_stops: List[TramStation], line_id):
        buttons = [
            InlineKeyboardButton(f"{tram_stop.order}. {tram_stop.name}  ", callback_data=Callbacks.TRAM_STATION.format(line_code=line_id, station_code=tram_stop.id))
            for tram_stop in tram_stops
        ]
        rows = self._chunk_buttons(buttons, 2)
        return InlineKeyboardMarkup(rows)
    
    def fgc_stations_menu(self, fgc_stations: List[FgcStation], line_id):
        buttons = [
            InlineKeyboardButton(f"{fgc_station.order}. {fgc_station.name} {'⚠️' if fgc_station.has_alerts else ''}  ", callback_data=Callbacks.FGC_STATION.format(line_code=line_id, station_code=fgc_station.id))
            for fgc_station in fgc_stations
        ]
        rows = self._chunk_buttons(buttons, 2)
        return InlineKeyboardMarkup(rows)
    
    def metro_station_access_menu(self, station_accesses: List[MetroAccess]):
        buttons = [
            InlineKeyboardButton(
                f"{"🛗 " if access.NUM_ASCENSORS > 0 else "🚶‍♂️"}{access.NOM_ACCES}",
                url = GoogleMapsHelper.build_directions_url(latitude=access.coordinates[1], longitude=access.coordinates[0])
            )
            for access in station_accesses
        ]
        rows = self._chunk_buttons(buttons, 2)
        return InlineKeyboardMarkup(rows)    
    
    def map_reply_menu(self, encoded):
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
    
    def update_menu(self, is_favorite: bool, item_type:str, item_id: str, line_id: str, previous_callback: str, has_connections: bool = False):
        if is_favorite:
            fav_button = InlineKeyboardButton(
                self.language_manager.t('keyboard.favorites.remove'),
                callback_data=Callbacks.REMOVE_FAVORITE.format(
                    item_type=item_type,
                    line_id=line_id,
                    item_id=item_id,
                    previous_callback=previous_callback.split(":")[0],
                    has_connections=has_connections
                )
            )
        else:
            fav_button = InlineKeyboardButton(
                self.language_manager.t('keyboard.favorites.add'),
                callback_data=Callbacks.ADD_FAVORITE.format(
                    item_type=item_type,
                    line_id=line_id,
                    item_id=item_id,
                    previous_callback=previous_callback.split(":")[0],
                    has_connections=has_connections
                )
            )
        
        inline_buttons = []
        if "station" not in previous_callback:
            inline_buttons.append(InlineKeyboardButton(f'{self.language_manager.t('common.next')}  ', callback_data=f"{item_type}_station:{line_id}:{item_id}"))
        if item_type == TransportType.METRO.value and "access" not in previous_callback:
            inline_buttons.append(InlineKeyboardButton(f'{self.language_manager.t('common.access')}  ', callback_data=f"{item_type}_access:{line_id}:{item_id}"))
        if has_connections and "connections" not in previous_callback:
            inline_buttons.append(InlineKeyboardButton(f'{self.language_manager.t('common.connections')}  ', callback_data=f"{item_type}_connections:{line_id}:{item_id}"))

        return InlineKeyboardMarkup([
            inline_buttons,
            [fav_button]
        ])
    
    def favorites_menu(self, favs):
        TRANSPORT_CONFIG = {
            TransportType.METRO.value: {
                "emoji": TransportType.METRO.emoji,
                "name_fmt": "{nom_linia} - {name}",
                "callback": lambda item: Callbacks.METRO_STATION.format(
                    line_code=item.get("codi_linia"),
                    station_code=item.get("code")
                ),
            },
            TransportType.BUS.value: {
                "emoji": TransportType.BUS.emoji,
                "name_fmt": "({code}) {name}",
                "callback": lambda item: Callbacks.BUS_STATION.format(
                    line_code=item.get("codi_linia"),
                    station_code=item.get("code")
                ),
            },
            TransportType.TRAM.value: {
                "emoji": TransportType.TRAM.emoji,
                "name_fmt": "{nom_linia} - {name}",
                "callback": lambda item: Callbacks.TRAM_STATION.format(
                    line_code=item.get("codi_linia"),
                    station_code=item.get("code")
                ),
            },
            TransportType.RODALIES.value: {
                "emoji": TransportType.RODALIES.emoji,
                "name_fmt": "{nom_linia} - {name}",
                "callback": lambda item: Callbacks.RODALIES_STATION.format(
                    line_code=item.get("codi_linia"),
                    station_code=item.get("code")
                ),
            },
            TransportType.BICING.value: {
                "emoji": TransportType.BICING.emoji,
                "name_fmt": "({code}) {name}",
                "callback": lambda item: Callbacks.BICING_STATION.format(
                    line_code='bicing',
                    station_code=item.get("code")
                ),
            },
            TransportType.FGC.value: {
                "emoji": TransportType.FGC.emoji,
                "name_fmt": "{nom_linia} - {name}",
                "callback": lambda item: Callbacks.FGC_STATION.format(
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
    
    def update_notifications(self, enabled_notifications: bool):
        locale_key, bool_value = ('disable', False) if enabled_notifications else ('enable', True)
        return InlineKeyboardMarkup([[InlineKeyboardButton(self.language_manager.t(f'keyboard.notifications.{locale_key}'), callback_data=Callbacks.SET_RECEIVE_NOTIFICATIONS.format(value=bool_value))]])
    
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

    def reply_keyboard_stations_menu(self, all_stops: list):
        """
        Generates an InlineKeyboardMarkup with all stops (metro, bus, tram),
        using the precomputed distances if available.
        
        Args:
            all_stops (list): List of dictionaries containing stop info and distance_km.

        Returns:
            InlineKeyboardMarkup: Keyboard markup ready to send to the user.
        """
        buttons = []

        for stop in all_stops:
            # Format distance if available
            distance_str = f" ({DistanceHelper.format_distance(stop['distance_km'])})" if stop.get("distance_km") is not None else ""

            # Build text and callback depending on type
            if stop["type"] == "metro":
                text = f"{TransportType.METRO.emoji} {stop['line_name']} - {stop['station_name']}{distance_str}"
                callback = Callbacks.METRO_STATION.format(
                    line_code=stop["line_code"],
                    station_code=stop["station_code"]
                )
            elif stop["type"] == "bus":
                text = f"{TransportType.BUS.emoji} ({stop['station_code']}) - {stop['station_name']}{distance_str}"
                callback = Callbacks.BUS_STATION.format(
                    line_code=stop["line_code"],
                    station_code=stop["station_code"]
                )
            elif stop["type"] == "tram":
                text = f"{TransportType.TRAM.emoji} {stop['line_name']} - {stop['station_name']}{distance_str}"
                callback = Callbacks.TRAM_STATION.format(
                    line_code=stop["line_code"],
                    station_code=stop["station_code"]
                )
            elif stop["type"] == "rodalies":
                text = f"{TransportType.RODALIES.emoji} {stop['line_name']} - {stop['station_name']}{distance_str}"
                callback = Callbacks.RODALIES_STATION.format(
                    line_code=stop["line_code"],
                    station_code=stop["station_code"]
                )
            elif stop["type"] == "bicing":
                text = f"{TransportType.BICING.emoji} {stop['station_name']} (🅿️:{stop['slots']} 🔋:{stop["electrical"]} 🚲:{stop["mechanical"]}){distance_str}"
                callback = Callbacks.BICING_STATION.format(
                    line_code='bicing',
                    station_code=stop["station_code"]
                )
            elif stop["type"] == "fgc":
                text = f"{TransportType.FGC.emoji} {stop['line_name']} - {stop['station_name']}{distance_str}"
                callback = Callbacks.FGC_STATION.format(
                    line_code=stop["line_code"],
                    station_code=stop["station_code"]
                )
            else:
                continue  # ignore unknown types

            buttons.append(InlineKeyboardButton(text, callback_data=callback))

        # Chunk buttons into rows
        rows = self._chunk_buttons(buttons, 1)
        return InlineKeyboardMarkup(rows)
    

    
    