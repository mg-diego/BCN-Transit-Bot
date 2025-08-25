from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory
from application import BusService, MessageService, UpdateManager
from providers.manager import UserDataManager, LanguageManager
from providers.helpers import TransportDataCompressor, logger
from domain.transport_type import TransportType

from .handler_base import HandlerBase

class BusHandler(HandlerBase):
    def __init__(
        self,
        keyboard_factory: KeyboardFactory,
        bus_service: BusService,
        update_manager: UpdateManager,
        user_data_manager: UserDataManager,
        message_service: MessageService,
        language_manager: LanguageManager
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager)
        self.keyboard_factory = keyboard_factory
        self.bus_service = bus_service
        self.mapper = TransportDataCompressor()

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):        
        """Display all bus lines (paginated menu)."""
        await self.show_transport_lines(
            update,
            context,
            transport_type=TransportType.BUS,
            service_get_lines=self.bus_service.get_all_lines,
            keyboard_menu_builder=self.keyboard_factory.bus_category_menu
        )
        '''
        bus_lines = await self.bus_service.get_all_lines()
        page = 0
        type = TransportType.BUS.value.capitalize()

        if self.message_service.check_query_callback(update, "bus_page:"):
            _, page = self.message_service.get_callback_data(update)
        else:
            await self.message_service.handle_interaction(update, self.language_manager.t("common.loading.lines", type=type))

        reply_markup = self.keyboard_factory.bus_lines_paginated_menu(bus_lines, int(page))
        await self.message_service.handle_interaction(update, self.language_manager.t("common.select.line", type=type), reply_markup)
        '''

    async def show_bus_category_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _, category = self.message_service.get_callback_data(update)
        lines = await self.bus_service.get_lines_by_category(category)
        await self.message_service.handle_interaction(
            update,
            self.language_manager.t('common.select.line', type=TransportType.BUS.value),
            reply_markup=self.keyboard_factory.bus_lines_menu(lines)
        )

    async def show_line_stops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display stops of a bus line."""
        self.message_service.set_bot_instance(context.bot)
        _, line_id, line_name = self.message_service.get_callback_data(update)

        line = await self.bus_service.get_line_by_id(line_id)
        stops = await self.bus_service.get_stops_by_line(line_id)
        encoded = self.mapper.map_bus_stops(stops, line_id, line.ORIGINAL_NOM_LINIA)

        await self.message_service.send_new_message_from_callback(
            update,
            text=self.language_manager.t('common.line.only.map', line=line_name),
            reply_markup=self.keyboard_factory.bus_stops_map_menu(encoded)
        )

    async def show_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display a specific bus stop with next arrivals."""
        user_id, chat_id, line_id, bus_stop_id = self.extract_context(update, context)
        logger.info(f"Showing stop info for user {user_id}, line {line_id}, stop {bus_stop_id}")

        bus_stop = await self.bus_service.get_stop_by_id(bus_stop_id)
        message = await self.show_stop_intro(update, context, TransportType.BUS.value, line_id, bus_stop_id, bus_stop.coordinates[1], bus_stop.coordinates[0], bus_stop.NOM_PARADA)
        await self.bus_service.get_stop_routes(bus_stop_id)
        await self.update_manager.stop_loading(update, context)

        async def update_text():
            next_buses = await self.bus_service.get_stop_routes(bus_stop_id)
            is_fav = self.user_data_manager.has_favorite(user_id, TransportType.BUS.value, bus_stop_id)
            text = f"🚉 {self.language_manager.t('bus.stop.next')}\n{next_buses}"
            keyboard = self.keyboard_factory.update_menu(is_fav, TransportType.BUS.value, bus_stop_id, line_id, user_id, previous_callback=self.message_service.get_callback_query(update))
            return text, keyboard

        self.start_update_loop(user_id, chat_id, message.message_id, get_text_callable=update_text)
        logger.info(f"Started update loop task for user {user_id}, station {bus_stop_id}")
