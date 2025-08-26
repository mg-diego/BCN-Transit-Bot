from domain.transport_type import TransportType
from telegram import Update
from telegram.ext import ContextTypes

from application import RodaliesService, MessageService, UpdateManager

from providers.manager import UserDataManager, LanguageManager
from providers.helpers import TransportDataCompressor, logger

from ui.keyboard_factory import KeyboardFactory
from .handler_base import HandlerBase


class RodaliesHandler(HandlerBase):
    """
    Handles metro-related user interactions in the bot.
    """

    def __init__(
        self,
        keyboard_factory: KeyboardFactory,
        rodalies_service: RodaliesService,
        update_manager: UpdateManager,
        user_data_manager: UserDataManager,
        message_service: MessageService,
        language_manager: LanguageManager
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager, keyboard_factory)
        self.rodalies_service = rodalies_service
        self.mapper = TransportDataCompressor()
        self.transport_type = TransportType.RODALIES.value
        logger.info(f"[{self.__class__.__name__}] RodaliesHandler initialized")

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Showing rodalies lines menu")
        type=TransportType.RODALIES.value.capitalize()
        await self.message_service.send_new_message(update, self.language_manager.t('common.loading.lines', type=type), reply_markup=self.keyboard_factory._back_reply_button())
        metro_lines = await self.rodalies_service.get_all_lines()
        reply_markup = self.keyboard_factory.rodalies_lines_menu(metro_lines)
        await self.message_service.handle_interaction(
            update,
            self.language_manager.t('common.select.line', type=type),
            reply_markup=reply_markup
        )

    async def show_line_stops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display stations of a rodalies line."""
        self.message_service.set_bot_instance(context.bot)
        _, line_id = self.message_service.get_callback_data(update)

        line = await self.rodalies_service.get_line_by_id(line_id)
        stops = await self.rodalies_service.get_stations_by_line(line_id)
        encoded = self.mapper.map_rodalies_stations(stops, line)

        await self.message_service.send_new_message_from_callback(
            update,
            text=self.language_manager.t('common.line.only.map', line=line.name),
            reply_markup=self.keyboard_factory.bus_stops_map_menu(encoded)
        )

    async def show_station(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display a specific rodalies station with next arrivals."""
        user_id, chat_id, line_id, rodalies_station_id = self.extract_context(update, context)
        logger.info(f"Showing station info for user {user_id}, line {line_id}, stop {rodalies_station_id}")
        callback = f"rodalies_station:{line_id}:{rodalies_station_id}"

        rodalies_station = await self.rodalies_service.get_station_by_id(rodalies_station_id, line_id)
        message = await self.show_stop_intro(update, context, self.transport_type, line_id, rodalies_station_id, rodalies_station.latitude, rodalies_station.longitude, rodalies_station.name)
        await self.rodalies_service.get_station_routes(rodalies_station_id, line_id)
        await self.update_manager.stop_loading(update, context)
        
        async def update_text():
            next_rodalies = await self.rodalies_service.get_station_routes(rodalies_station_id, line_id)
            is_fav = self.user_data_manager.has_favorite(user_id, self.transport_type, rodalies_station_id)
            text = f"🚉 {self.language_manager.t(f'{self.transport_type}.station.next')}\n{next_rodalies}"
            keyboard = self.keyboard_factory.update_menu(is_fav, self.transport_type, rodalies_station_id, line_id, user_id)
            return text, keyboard

        self.start_update_loop(user_id, chat_id, message.message_id, get_text_callable=update_text, previous_callback=callback)
        logger.info(f"Started update loop task for user {user_id}, station {rodalies_station_id}")
        