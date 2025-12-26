import asyncio
from domain.bicing import BicingStation
from domain.common.location import Location
from domain.transport_type import TransportType
from providers.helpers.distance_helper import DistanceHelper
from providers.manager import audit_action
from telegram import Update
from telegram.ext import (
    ContextTypes
)

from providers.helpers.transport_data_compressor import TransportDataCompressor
from ui import MetroHandler, BusHandler, TramHandler, RodaliesHandler, FavoritesHandler, LanguageHandler, HelpHandler, MenuHandler, SettingsHandler, BicingHandler, NotificationsHandler, FgcHandler

class ReplyHandler:
    def __init__(
            self,
            menu_handler: MenuHandler,
            metro_handler: MetroHandler,
            bus_handler: BusHandler,
            tram_handler: TramHandler,
            rodalies_handler: RodaliesHandler,
            favorites_handler: FavoritesHandler,
            language_handler: LanguageHandler,
            help_handler: HelpHandler,
            settings_handler: SettingsHandler,
            bicing_handler: BicingHandler,
            fgc_handler: FgcHandler,
            notifications_handler: NotificationsHandler
        ):

        self.menu_handler = menu_handler
        self.metro_handler = metro_handler
        self.bus_handler = bus_handler
        self.tram_handler = tram_handler
        self.rodalies_handler = rodalies_handler
        self.favorites_handler = favorites_handler
        self.language_handler = language_handler
        self.help_handler = help_handler
        self.settings_handler = settings_handler
        self.bicing_handler = bicing_handler
        self.fgc_handler = fgc_handler
        self.notifications_handler = notifications_handler

        self.mapper = TransportDataCompressor()

        self.previous_search = None
        self.current_search = None

    async def reply_router(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.current_search = str(update.message.text)

        if self.current_search == f"{TransportType.METRO.emoji} Metro":
            await self.metro_handler.show_lines(update, context)
        elif self.current_search == f"{TransportType.BUS.emoji} Bus":
            await self.bus_handler.show_bus_categories(update, context)
        elif self.current_search == f"{TransportType.TRAM.emoji} Tram":
            await self.tram_handler.show_lines(update, context)
        elif self.current_search == f"{TransportType.RODALIES.emoji} Rodalies":
            await self.rodalies_handler.show_lines(update, context)
        elif self.current_search == f"{TransportType.BICING.emoji} Bicing":
            await self.bicing_handler.show_instructions(update, context)    
        elif self.current_search == f"{TransportType.FGC.emoji} FGC":
            await self.fgc_handler.show_lines(update, context)
        elif '⭐' in self.current_search:
            await self.favorites_handler.show_favorites(update, context)
        elif '🌐' in self.current_search:
            await self.language_handler.show_languages(update, context)
        elif '📘' in self.current_search:
            await self.help_handler.show_help(update, context)
        elif '⚙️' in self.current_search:
            await self.settings_handler.show_settings(update, context)
        elif '🔔' in self.current_search:
            await self.notifications_handler.show_current_configuration(update, context)
        elif '🔍' in self.current_search:
            await self.menu_handler.back_to_menu(update, context)
        elif '📍' in self.current_search:
            await self.handle_nearby(update, context)
        else:
            await self.handle_reply_from_user(update, context)
        
        self.previous_search = self.current_search

    async def handle_nearby(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_location = None):
        message_service = self.menu_handler.message_service
        language_manager = self.menu_handler.language_manager
        keyboard_factory = self.menu_handler.keyboard_factory

        message_service.set_bot_instance(context.bot)

        if user_location is None:
            await message_service.send_new_message(update, language_manager.t('results.location.ask'), keyboard_factory.location_keyboard())
            self.previous_search = None
            self.current_search = None
        else:
            await message_service.send_new_message(update, language_manager.t('results.location.received'))
            metro_stations, bus_stops, tram_stops, rodalies_stations, bicing_stations, fgc_stations = await self._search_stations('', only_bicing=False)
            near_stops = DistanceHelper.build_stops_list(metro_stations, bus_stops, tram_stops, rodalies_stations, bicing_stations, fgc_stations, user_location, results_to_return=999999, max_distance_km=0.5)
            encoded = self.mapper.map_near_stations(near_stops, user_location)
            
            await message_service.send_new_message(update, language_manager.t('common.map.open'), keyboard_factory.map_reply_menu(encoded))


    @audit_action(action_type="REPLY_ROUTER", params_args=["user_location", "only_bicing"])
    async def handle_reply_from_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_location = None, only_bicing = False):        
        message_service = self.menu_handler.message_service
        update_manager = self.menu_handler.update_manager
        language_manager = self.menu_handler.language_manager
        keyboard_factory = self.menu_handler.keyboard_factory

        if user_location is None:
            await message_service.send_new_message(update, language_manager.t('results.location.ask'), keyboard_factory.location_keyboard())
            self.current_search = str(update.message.text)        
        else:
            user_location = Location(latitude=user_location.latitude, longitude=user_location.longitude)
            
        message_service.set_bot_instance(context.bot)

        if len(self.current_search) < 3:
            await update.message.reply_text(language_manager.t('results.minimum.letters'))
            return

        message = await update_manager.start_loading(update, context, language_manager.t('results.searching'))
        chat_id = message_service.get_chat_id(update)
        await update_manager.stop_loading(update, context)

        metro_stations, bus_stops, tram_stops, rodalies_stations, bicing_stations, fgc_stations = await self._search_stations(self.current_search, only_bicing)
        stops_with_distance = DistanceHelper.build_stops_list(metro_stations, bus_stops, tram_stops, rodalies_stations, bicing_stations, fgc_stations, user_location)
        if not only_bicing:
            metro_count = len([s for s in stops_with_distance if s["type"] == TransportType.METRO.value])
            bus_count = len([s for s in stops_with_distance if s["type"] == TransportType.BUS.value])
            tram_count = len([s for s in stops_with_distance if s["type"] == TransportType.TRAM.value])
            rodalies_count = len([s for s in stops_with_distance if s["type"] == TransportType.RODALIES.value])
            bicing_count = len([s for s in stops_with_distance if s["type"] == TransportType.BICING.value])
            fgc_count = len([s for s in stops_with_distance if s["type"] == TransportType.FGC.value])

            msg = language_manager.t(
                "results.found",
                count=len(stops_with_distance),
                search_value=self.current_search,
                metro_results=metro_count,
                bus_results=bus_count,
                tram_results=tram_count,
                rodalies_results=rodalies_count,
                bicing_results=bicing_count,
                fgc_results=fgc_count
            )
        else:
            near_bicing_stations = [
                BicingStation(
                    streetName=stop.get('station_name'),
                    id=stop.get('station_code'),
                    latitude=stop.get('coordinates')[0],
                    longitude=stop.get('coordinates')[1],
                    slots=stop.get('slots'),
                    mechanical_bikes=stop.get('mechanical'),
                    electrical_bikes=stop.get('electrical'),
                    type=None,
                    streetNumber=None,
                    bikes=None,
                    type_bicing=None,
                    status=None,
                    disponibilidad=stop.get('availability'),
                    icon='',
                    transition_end=None,
                    transition_start=None,
                    obcn=None,
                )
                for stop in stops_with_distance
            ]
            encoded = self.mapper.map_bicing_stations(near_bicing_stations, user_location)
            await message_service.send_new_message(update, language_manager.t('results.location.received'), keyboard_factory.map_reply_menu(encoded))
            self.current_search = self.previous_search
            msg = language_manager.t('bicing.station.near')

        await message_service.edit_message_by_id(
            chat_id,
            message.message_id,
            msg,
            keyboard_factory.reply_keyboard_stations_menu(stops_with_distance)
        )

    async def _search_stations(self, value_to_search: str, only_bicing: bool = False):     
        metro_service = self.metro_handler.metro_service
        bus_service = self.bus_handler.bus_service
        tram_service = self.tram_handler.tram_service
        rodalies_service = self.rodalies_handler.rodalies_service
        bicing_service = self.bicing_handler.bicing_service
        fgc_service = self.fgc_handler.fgc_service

        metro_stations = []
        bus_stops = []
        tram_stops = []
        rodalies_stations = []
        bicing_stations = []
        fgc_stations = []

        if only_bicing: 
            bicing_stations = await bicing_service.get_all_stations()

        elif value_to_search.isdigit(): # ONLY FOR BUS STOPS AND BICING
            bicing = await bicing_service.get_station_by_id(value_to_search)
            if bicing is not None:
                bicing_stations.append(bicing)

            stop = await bus_service.get_stop_by_code(value_to_search)
            if stop is not None:
                bus_stops.append(stop)

        else: # METRO STATIONS | BUS STOPS | TRAM STOPS | RODALIES STATIONS | BICING STATIONS | FGC STATIONS
            metro_task = metro_service.get_stations_by_name(value_to_search)
            bus_task = bus_service.get_stops_by_name(value_to_search)
            tram_task = tram_service.get_stops_by_name(value_to_search)
            rodalies_task = rodalies_service.get_stations_by_name(value_to_search)
            bicing_task = bicing_service.get_stations_by_name(value_to_search)
            fgc_task = fgc_service.get_stations_by_name(value_to_search)

            (
                metro_stations,
                bus_stops,
                tram_stops,
                rodalies_stations,
                bicing_stations,
                fgc_stations,
            ) = await asyncio.gather(
                metro_task,
                bus_task,
                tram_task,
                rodalies_task,
                bicing_task,
                fgc_task
            )

        return metro_stations, bus_stops, tram_stops, rodalies_stations, bicing_stations, fgc_stations

    @audit_action(action_type="LOCATION_HANDLER")
    async def location_handler(self, update, context):
        if self.previous_search == "🚴 Bicing":
            await self.handle_reply_from_user(update, context, update.message.location, only_bicing=True)
        elif self.previous_search is not None:
            await self.handle_reply_from_user(update, context, update.message.location)
        else:
            await self.handle_nearby(update, context, update.message.location)
                