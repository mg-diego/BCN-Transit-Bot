from enum import Enum

from domain.transport_type import TransportType


class Callbacks(Enum):
    MENU_CALLBACK = "menu"
    MENU_METRO_CALLBACK = TransportType.METRO.value
    MENU_BUS_CALLBACK = TransportType.BUS.value
    MENU_TRAM_CALLBACK = TransportType.TRAM.value
    MENU_RODALIES_CALLBACK = TransportType.RODALIES.value
    MENU_FAVORITES_CALLBACK = "favorites"
    MENU_LANGUAGE_CALLBACK = "language"
    MENU_HELP_CALLBACK = "help"
    BACK_TO_MENU_CALLBACK = "back_to_menu"

    METRO_LINE = "metro_line:{line_code}:{line_name}"
    BUS_LINE = "bus_line:{line_code}:{line_name}"
    TRAM_LINE = "tram_line:{line_code}:{line_name}"
    RODALIES_LINE = "rodalies_line:{line_code}"

    METRO_STATION = "metro_station:{line_code}:{station_code}"
    BUS_STOP = "bus_stop:{line_code}:{stop_code}"
    TRAM_STOP = "tram_stop:{line_code}:{stop_code}"
    RODALIES_STATION = "rodalies_station:{line_code}:{station_code}"

    BUS_CATEGORY_D = "bus_category:Diagonals"
    BUS_CATEGORY_H = "bus_category:Horitzontals"
    BUS_CATEGORY_V = "bus_category:Verticals"
    BUS_CATEGORY_M = "bus_category:Llançadores"
    BUS_CATEGORY_X = "bus_category:XPRESBus"
    BUS_CATEGORY_1_60 = "bus_category:1-60"
    BUS_CATEGORY_61_100 = "bus_category:61-100"
    BUS_CATEGORY_101_120 = "bus_category:101-120"
    BUS_CATEGORY_121_140 = "bus_category:121-140"
    BUS_CATEGORY_141_200 = "bus_category:141-200"

    REMOVE_FAVORITE = "remove_fav:{item_type}:{line_id}:{item_id}:{previous_callback}:{has_connections}"
    ADD_FAVORITE = "add_fav:{item_type}:{line_id}:{item_id}:{previous_callback}:{has_connections}"

    SET_LANGUAGE = "set_language:{language_code}"

    def format(self, **kwargs):
        return self.value.format(**kwargs)