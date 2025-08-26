from domain.transport_type import TransportType

from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory

from application import TramService, UpdateManager, MessageService

from providers.manager import UserDataManager, LanguageManager
from providers.helpers import TransportDataCompressor, logger

from ui.transport.handler_base import HandlerBase

class TramHandler(HandlerBase):
    """
    Handles tram-related user interactions in the bot.
    """

    def __init__(
        self,
        keyboard_factory: KeyboardFactory,
        tram_service: TramService,
        update_manager: UpdateManager,
        user_data_manager: UserDataManager,
        message_service: MessageService,
        language_manager: LanguageManager
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager, keyboard_factory)
        self.tram_service = tram_service
        self.mapper = TransportDataCompressor()
        logger.info(f"[{self.__class__.__name__}] TramHandler initialized")

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_transport_lines(
            update,
            context,
            transport_type=TransportType.TRAM,
            service_get_lines=self.tram_service.get_all_lines,
            keyboard_menu_builder=self.keyboard_factory.tram_lines_menu
        )

    async def ask_search_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await super().ask_search_method(update, context, transport_type=TransportType.TRAM)

    async def show_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_line_stations_list(
            update,
            context,
            transport_type=TransportType.TRAM,
            service_get_stations_by_line=self.tram_service.get_stops_by_line,
            keyboard_menu_builder=self.keyboard_factory.tram_stops_menu
        )

    async def show_map(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_line_map(
            update,
            context,
            transport_type=TransportType.TRAM,
            service_get_stations_by_line=self.tram_service.get_stops_by_line,
            mapper_method=self.mapper.map_tram_stops,
            keyboard_menu_builder=self.keyboard_factory.bus_stops_map_menu
        )

    async def show_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show details for a specific tram stop and start update loop."""
        user_id, chat_id, line_id, stop_id = self.extract_context(update, context)
        logger.info(f"Showing stop info for user {user_id}, line {line_id}, stop {stop_id}")

        stop = await self.tram_service.get_stop_by_id(stop_id, line_id)
        message = await self.show_stop_intro(update, context, TransportType.TRAM.value, line_id, stop_id, stop.latitude, stop.longitude, stop.name)
        await self.tram_service.get_stop_routes(stop.outboundCode, stop.returnCode)
        await self.update_manager.stop_loading(update, context)

        async def update_text():
            routes = await self.tram_service.get_stop_routes(stop.outboundCode, stop.returnCode)
            text = (
                f"🚉 {self.language_manager.t('tram.stop.next')}\n{routes} \n\n"
            )
            is_fav = self.user_data_manager.has_favorite(user_id, "tram", stop_id)
            keyboard = self.keyboard_factory.update_menu(is_fav, "tram", stop_id, line_id, user_id, previous_callback=self.message_service.get_callback_query(update))
            return text, keyboard
        
        self.start_update_loop(user_id, chat_id, message.message_id, update_text)
        logger.info(f"Started update loop task for user {user_id}, stop {stop_id}")
