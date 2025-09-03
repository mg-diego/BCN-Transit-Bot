from domain.transport_type import TransportType
from domain.metro import get_alert_by_language, format_metro_connections
from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory

from application import MetroService, UpdateManager, MessageService, TelegraphService

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
        metro_service: MetroService,
        update_manager: UpdateManager,
        user_data_manager: UserDataManager,
        message_service: MessageService,
        language_manager: LanguageManager,
        telegraph_service: TelegraphService
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager, keyboard_factory, telegraph_service)
        self.metro_service = metro_service
        self.mapper = TransportDataCompressor()
        logger.info(f"[{self.__class__.__name__}] FgcHandler initialized")


    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.message_service.handle_interaction(update, '⚠️ Development in process, it will be available in next versions.')
