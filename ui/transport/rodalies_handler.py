from domain.transport_type import TransportType
from telegram import Update
from telegram.ext import ContextTypes

from application import RodaliesService, MessageService, UpdateManager

from providers.manager import UserDataManager, LanguageManager
from providers.helpers import Mapper, logger

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
        super().__init__(message_service, update_manager, language_manager, user_data_manager)
        self.keyboard_factory = keyboard_factory
        self.rodalies_service = rodalies_service
        self.mapper = Mapper()
        logger.info(f"[{self.__class__.__name__}] RodaliesHandler initialized")

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Showing rodalies lines menu")
        type=TransportType.RODALIES.value.capitalize()
        await self.message_service.edit_inline_message(update, self.language_manager.t('common.loading', type=type))
        metro_lines = await self.rodalies_service.get_all_lines()
        reply_markup = self.keyboard_factory.rodalies_lines_menu(metro_lines)
        await self.message_service.edit_inline_message(
            update,
            self.language_manager.t('common.select.line', type=type),
            reply_markup=reply_markup
        )

    async def show_line_stops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display stations of a rodalies line."""
        self.message_service.set_bot_instance(context.bot)
        _, line_id = self.message_service.get_callback_data(update)

        line = await self.rodalies_service.get_line_by_id(line_id)
        stops = await self.rodalies_service.get_stops_by_line(line_id)
        encoded = self.mapper.map_rodalies_stations(stops, line_id, line.name, line.color)

        await self.message_service.send_new_message_from_callback(
            update,
            text=self.language_manager.t('bus.line.stops', line_name=line.name),
            reply_markup=self.keyboard_factory.bus_stops_map_menu(encoded)
        )