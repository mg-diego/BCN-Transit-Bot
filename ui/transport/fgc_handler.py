from domain.transport_type import TransportType
from domain.metro import get_alert_by_language, format_metro_connections
from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory

from application import FgcService, UpdateManager, MessageService, TelegraphService

from providers.manager import UserDataManager
from providers.manager import LanguageManager
from providers.helpers import TransportDataCompressor, GoogleMapsHelper, logger

from .handler_base import HandlerBase

class FgcHandler(HandlerBase):
    """
    Handles metro-related user interactions in the bot.
    """

    def __init__(
        self,
        keyboard_factory: KeyboardFactory,
        fgc_service: FgcService,
        update_manager: UpdateManager,
        user_data_manager: UserDataManager,
        message_service: MessageService,
        language_manager: LanguageManager,
        telegraph_service: TelegraphService
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager, keyboard_factory, telegraph_service)
        self.fgc_service = fgc_service
        self.mapper = TransportDataCompressor()
        logger.info(f"[{self.__class__.__name__}] FgcHandler initialized")


    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_transport_lines(
            update,
            context,
            transport_type=TransportType.FGC,
            service_get_lines=self.fgc_service.get_all_lines,
            keyboard_menu_builder=self.keyboard_factory.fgc_lines_menu
        )

    async def ask_search_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await super().ask_search_method(update, context, transport_type=TransportType.FGC)

    async def show_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_line_stations_list(
            update,
            context,
            transport_type=TransportType.FGC,
            service_get_stations_by_line=self.fgc_service.get_stations_by_line,
            keyboard_menu_builder=self.keyboard_factory.fgc_stations_menu
        )

    async def show_station(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.message_service.handle_interaction(update, "🚧 This feature isn't available yet, but it's coming in a future update!")
