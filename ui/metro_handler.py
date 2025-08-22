import json
from domain.transport_type import TransportType
from telegram import Update
from telegram.ext import ContextTypes
from providers import logger

from ui.keyboard_factory import KeyboardFactory
from application.metro_service import MetroService
from application.update_manager import UpdateManager
from application.message_service import MessageService
from providers.user_data_manager import UserDataManager
from providers.language_manager import LanguageManager
from providers.mapper import Mapper

from ui.handler_base import HandlerBase  # <-- hereda el update loop

class MetroHandler(HandlerBase):
    """
    Handles metro-related user interactions in the bot.
    """

    def __init__(
        self,
        keyboard_factory: KeyboardFactory,
        metro_service: MetroService,
        update_manager: UpdateManager,
        user_data_manager: UserDataManager,
        message_service: MessageService,
        language_manager: LanguageManager
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager)
        self.keyboard_factory = keyboard_factory
        self.metro_service = metro_service
        self.mapper = Mapper()
        logger.info(f"[{self.__class__.__name__}] MetroHandler initialized")

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Showing metro lines menu")
        await self.message_service.edit_inline_message(update, self.language_manager.t('metro.loading'))
        metro_lines = await self.metro_service.get_all_lines()
        reply_markup = self.keyboard_factory.metro_lines_menu(metro_lines)
        await self.message_service.edit_inline_message(
            update,
            self.language_manager.t('metro.select.line'),
            reply_markup=reply_markup
        )

    async def show_line_stations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _, line_id = self.message_service.get_callback_data(update)
        logger.info(f"Showing stations for metro line {line_id}")
        line = await self.metro_service.get_line_by_id(line_id)
        stations = await self.metro_service.get_stations_by_line(line_id)
        reply_markup = self.keyboard_factory.metro_stations_menu(stations, line_id)
        await self.message_service.edit_inline_message(
            update,
            self.language_manager.t("metro.line.stations", line_id=line.NOM_LINIA),
            reply_markup=reply_markup
        )

    async def show_map(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _, line_id = self.message_service.get_callback_data(update)
        line = await self.metro_service.get_line_by_id(line_id)
        stations = await self.metro_service.get_stations_by_line(line_id)
        encoded = self.mapper.map_metro_stations(stations, line_id, line.ORIGINAL_NOM_LINIA)
        logger.info(f"Showing map for metro line {line.ORIGINAL_NOM_LINIA} (ID: {line_id})")
        await self.message_service.send_new_message_from_callback(
            update=update,
            text=self.language_manager.t('bus.line.stops', line_name=line.ORIGINAL_NOM_LINIA),
            reply_markup=self.keyboard_factory.bus_stops_map_menu(encoded),
        )

    async def show_station(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id, chat_id, line_id, metro_station_id = self.extract_context(update, context)        
        logger.info(f"Showing station info for user {user_id}, line {line_id}, station {metro_station_id}")

        station = await self.metro_service.get_station_by_id(metro_station_id, line_id)      
        station_accesses = await self.metro_service.get_station_accesses(station.CODI_GRUP_ESTACIO)  
        message = await self.show_stop_intro(update, TransportType.METRO.value, line_id, metro_station_id, station.coordinates[1], station.coordinates[0], station.NOM_ESTACIO, self.keyboard_factory.metro_station_access_menu(station_accesses))

        station_connections = await self.metro_service.get_metro_station_connections(metro_station_id)
        station_alerts = await self.metro_service.get_metro_station_alerts(line_id, metro_station_id)

        # Define the async update function for HandlerBase
        async def update_text():
            routes = await self.metro_service.get_station_routes(metro_station_id)
            text = (
                f"🚉 {self.language_manager.t('metro.station.next')}\n{routes} \n\n"
                f"🔛 {self.language_manager.t('metro.station.connections')}\n{station_connections}\n\n"
                f"🚨 {self.language_manager.t('metro.station.alerts')}\n{station_alerts}"
            )
            is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, metro_station_id)
            keyboard = self.keyboard_factory.update_menu(is_fav, TransportType.METRO.value, metro_station_id, line_id, user_id)
            return text, keyboard

        # Start periodic update loop using HandlerBase
        self.start_update_loop(user_id, chat_id, message.message_id, update_text)
        logger.info(f"Started update loop task for user {user_id}, station {metro_station_id}")

    async def close_updates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _, user_id_str = self.message_service.get_callback_data(update)
        user_id = int(user_id_str)
        logger.info(f"Stopping updates for user {user_id}")

        self.update_manager.cancel_task(user_id)
        await self.message_service.edit_inline_message(update, self.language_manager.t('search.cleaning'))
        await self.message_service.clear_user_messages(user_id)
        await self.message_service.send_new_message_from_callback(update, self.language_manager.t('search.finish'))
        logger.info(f"Updates stopped and messages cleared for user {user_id}")
