import asyncio
import json
from domain.transport_type import TransportType
from providers.mapper import Mapper
from telegram import Update
from telegram.ext import ContextTypes
from providers import logger

from ui.keyboard_factory import KeyboardFactory
from application.tram_service import TramService
from application.update_manager import UpdateManager
from application.message_service import MessageService
from providers.user_data_manager import UserDataManager
from providers.language_manager import LanguageManager

from ui.handler_base import HandlerBase

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
        super().__init__(message_service, update_manager, language_manager, user_data_manager)
        self.keyboard_factory = keyboard_factory
        self.tram_service = tram_service
        self.user_data_manager = user_data_manager
        self.language_manager = language_manager
        self.mapper = Mapper()
        logger.info(f"[{self.__class__.__name__}] TramHandler initialized")

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info("Showing tram lines menu")
        await self.message_service.edit_inline_message(update, self.language_manager.t('tram.loading'))
        tram_lines = await self.tram_service.get_all_lines()
        reply_markup = self.keyboard_factory.tram_lines_menu(tram_lines)
        await self.message_service.edit_inline_message(
            update,
            self.language_manager.t('tram.select.line'),
            reply_markup=reply_markup
        )

    async def show_line_stops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _, line_id, line_name = self.message_service.get_callback_data(update)
        logger.info(f"Showing stops for tram line {line_name} (ID: {line_id})")

        stops = await self.tram_service.get_stops_by_line(line_id)
        reply_markup = self.keyboard_factory.tram_stops_menu(stops, line_id)
        await self.message_service.edit_inline_message(
            update,
            self.language_manager.t("tram.line.stops", line_id=line_name),
            reply_markup=reply_markup
        )

    async def show_map(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _, line_id = self.message_service.get_callback_data(update)
        line = await self.tram_service.get_line_by_id(line_id)
        stops = await self.tram_service.get_stops_by_line(line_id)
        logger.info(f"Showing map for tram line {line.original_name} (ID: {line_id})")

        encoded = self.mapper.map_tram_stops(stops, line_id, line.original_name)
        await self.message_service.send_new_message_from_callback(
            update=update,
            text=self.language_manager.t('bus.line.stops', line_name=line.original_name),
            reply_markup=self.keyboard_factory.bus_stops_map_menu(encoded),
        )

    async def show_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show details for a specific tram stop and start update loop."""
        user_id, chat_id, line_id, stop_id = self.extract_context(update, context)
        logger.info(f"Showing stop info for user {user_id}, line {line_id}, stop {stop_id}")

        stop = await self.tram_service.get_stop_by_id(stop_id, line_id)
        message = await self.show_stop_intro(update, TransportType.TRAM.value, line_id, stop_id, stop.latitude, stop.longitude, stop.name)

        async def update_text():
            routes = await self.tram_service.get_stop_routes(stop.outboundCode, stop.returnCode)
            text = (
                f"🚉 {self.language_manager.t('tram.stop.next')}\n{routes} \n\n"
            )
            is_fav = self.user_data_manager.has_favorite(user_id, "tram", stop_id)
            keyboard = self.keyboard_factory.update_menu(is_fav, "tram", stop_id, line_id, user_id)
            return text, keyboard
        
        self.start_update_loop(user_id, chat_id, message.message_id, update_text)
        logger.info(f"Started update loop task for user {user_id}, stop {stop_id}")
