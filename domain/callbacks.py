from enum import Enum

class Callbacks(Enum):
    MENU_CALLBACK = "menu"
    BACK_TO_MENU_CALLBACK = "back_to_menu"

    METRO_LINE = "metro_line:{line_code}:{line_name}"
    BUS_LINE = "bus_line:{line_code}:{line_name}"
    TRAM_LINE = "tram_line:{line_code}:{line_name}"
    RODALIES_LINE = "rodalies_line:{line_code}"
    FGC_LINE = "fgc_line:{line_code}:{line_name}"

    METRO_STATION = "metro_station:{line_code}:{station_code}"
    BUS_STATION = "bus_station:{line_code}:{station_code}"
    TRAM_STATION = "tram_station:{line_code}:{station_code}"
    RODALIES_STATION = "rodalies_station:{line_code}:{station_code}"
    BICING_STATION = "bicing_station:{line_code}:{station_code}"
    FGC_STATION = "fgc_station:{line_code}:{station_code}"

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

    SET_RECEIVE_NOTIFICATIONS = "set_receive_notifications:{value}"

    def format(self, **kwargs):
        return self.value.format(**kwargs)