from telegram import Update
from telegram.ext import ContextTypes
from ui.keyboard_factory import KeyboardFactory
from .handler_base import HandlerBase

from application import BicingService, UpdateManager, MessageService
from providers.helpers import TransportDataCompressor, logger
from providers.manager import LanguageManager, UserDataManager


class BicingHandler(HandlerBase):

    def __init__(
        self,
        keyboard_factory: KeyboardFactory,
        bicing_service: BicingService,
        update_manager: UpdateManager,
        user_data_manager: UserDataManager,
        message_service: MessageService,
        language_manager: LanguageManager
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager, keyboard_factory)
        self.bicing_service = bicing_service
        self.mapper = TransportDataCompressor()

    async def show_stations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.message_service.set_bot_instance(context.bot)

        stations = await self.bicing_service.get_stations()
        encoded = self.mapper.map_bicing_stations(stations)

        await self.message_service.send_new_message_from_callback(
            update,
            text=self.language_manager.t('common.line.only.map', line=''),  # INVESTIGATE TELEGRAPH TO SHOW ALERTS
            reply_markup=self.keyboard_factory.bus_stops_map_menu(encoded)
        )