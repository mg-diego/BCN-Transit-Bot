from domain.transport_type import TransportType
from providers.helpers.distance_helper import DistanceHelper
from telegram import Update
from telegram.ext import (
    ContextTypes
)

from ui import MetroHandler, BusHandler, TramHandler, RodaliesHandler, FavoritesHandler, LanguageHandler, HelpHandler, MenuHandler, SettingsHandler, BicingHandler

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
            bicing_handler: BicingHandler
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

        self.previous_search = None

    async def reply_router(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        btn_text = str(update.message.text)

        if btn_text == "🚇 Metro":
            await self.metro_handler.show_lines(update, context)
        elif btn_text == "🚌 Bus":
            await self.bus_handler.show_lines(update, context)
        elif btn_text == "🚋 Tram":
            await self.tram_handler.show_lines(update, context)
        elif btn_text == "🚆 Rodalies":
            await self.rodalies_handler.show_lines(update, context)        
        elif btn_text == '🚲 Bicing':
            await self.bicing_handler.show_instructions(update, context)
        elif '⭐' in btn_text:
            await self.favorites_handler.show_favorites(update, context)
        elif '🌐' in btn_text:
            await self.language_handler.show_languages(update, context)
        elif '📘' in btn_text:
            await self.help_handler.show_help(update, context)
        elif '⚙️' in btn_text:
            await self.settings_handler.show_settings(update, context)
        elif '🔔' in btn_text:
            pass
        elif '🔙' in btn_text:
            await self.menu_handler.back_to_menu(update, context)
        else:
            await self.handle_reply_from_user(update, context)

    async def handle_reply_from_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_location = None):
        message_service = self.menu_handler.message_service
        update_manager = self.menu_handler.update_manager
        language_manager = self.menu_handler.language_manager
        keyboard_factory = self.menu_handler.keyboard_factory

        metro_service = self.metro_handler.metro_service
        bus_service = self.bus_handler.bus_service
        tram_service = self.tram_handler.tram_service
        rodalies_service = self.rodalies_handler.rodalies_service
        bicing_service = self.bicing_handler.bicing_service

        if user_location is None:
            await message_service.send_new_message(update, language_manager.t('results.location.ask'), keyboard_factory.location_keyboard())
            search_text = str(update.message.text)            
        else:
            await message_service.send_new_message(update, language_manager.t('results.location.received'), keyboard_factory._back_reply_button())
            search_text = self.previous_search

        self.previous_search = search_text
        message_service.set_bot_instance(context.bot)

        if len(search_text) < 3:
            await update.message.reply_text(language_manager.t('results.minimum.letters'))
            return
        
        message = await update_manager.start_loading(update, context, language_manager.t('results.searching'))
        chat_id = message_service.get_chat_id(update)

        metro_stations = []
        bus_stops = []
        tram_stops = []
        rodalies_stations = []
        bicing_stations = []

        if search_text.isdigit(): # ONLY FOR BUS STOPS AND BICING
            bicing = await bicing_service.get_station_by_id(search_text)
            if bicing is not None:
                bicing_stations.append(bicing)
            stop = await bus_service.get_stop_by_id(search_text)
            if stop is not None:
                bus_stops.append(stop)

        else: # METRO STATIONS | BUS STOPS | TRAM STOPS | RODALIES STATIONS
            tram_stops = [] #await tram_service.get_stops_by_name(search_text)
            metro_stations = [] # await metro_service.get_stations_by_name(search_text)
            bus_stops = [] #await bus_service.get_stops_by_name(search_text)
            rodalies_stations =[] # await rodalies_service.get_stations_by_name(search_text)
            bicing_stations = await bicing_service.get_stations_by_name(search_text)
        
        await update_manager.stop_loading(update, context)

        stops_with_distance = DistanceHelper.build_stops_list(metro_stations, bus_stops, tram_stops, rodalies_stations, bicing_stations, user_location)
        metro_count = len([s for s in stops_with_distance if s["type"] == TransportType.METRO.value])
        bus_count = len([s for s in stops_with_distance if s["type"] == TransportType.BUS.value])
        tram_count = len([s for s in stops_with_distance if s["type"] == TransportType.TRAM.value])
        rodalies_count = len([s for s in stops_with_distance if s["type"] == TransportType.RODALIES.value])
        bicing_count = len([s for s in stops_with_distance if s["type"] == TransportType.BICING.value])

        await message_service.edit_message_by_id(
            chat_id,
            message.message_id,
            language_manager.t(
                "results.found",
                count=len(stops_with_distance),
                search_value=search_text,
                metro_results=metro_count,
                bus_results=bus_count,
                tram_results=tram_count,
                rodalies_results=rodalies_count,
                bicing_results=bicing_count
            ),
            keyboard_factory.reply_keyboard_stations_menu(stops_with_distance)
        )

    async def location_handler(self, update, context):
        if self.previous_search is not None:
            await self.handle_reply_from_user(update, context, update.message.location)
                