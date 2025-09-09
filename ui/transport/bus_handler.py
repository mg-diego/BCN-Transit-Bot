from telegram import Update
from telegram.ext import ContextTypes

from domain.bus.bus_stop import get_alert_by_language
from domain.callbacks import Callbacks
from providers.helpers.google_maps_helper import GoogleMapsHelper
from ui.keyboard_factory import KeyboardFactory
from application import BusService, MessageService, UpdateManager, TelegraphService
from providers.manager import UserDataManager, LanguageManager
from providers.helpers import TransportDataCompressor, logger
from providers.manager import audit_action
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
        language_manager: LanguageManager,
        telegraph_service: TelegraphService
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager, keyboard_factory, telegraph_service)
        self.bus_service = bus_service
        self.audit_logger = self.user_data_manager.audit_logger
        self.mapper = TransportDataCompressor()

    async def show_bus_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):        
        """Display all bus lines (paginated menu)."""
        await self.show_transport_lines(
            update,
            context,
            transport_type=TransportType.BUS,
            service_get_lines=self.bus_service.get_all_lines,
            keyboard_menu_builder=self.keyboard_factory.bus_category_menu
        )

    @audit_action(action_type="SEARCH", command_or_button="show_lines")
    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _, category = self.message_service.get_callback_data(update)
        lines = await self.bus_service.get_lines_by_category(category)
        await self.message_service.handle_interaction(
            update,
            self.language_manager.t('common.select.line', type=TransportType.BUS.value),
            reply_markup=self.keyboard_factory.bus_lines_menu(lines)
        )

    @audit_action(action_type="SEARCH", command_or_button="show_bus_stops")
    async def show_line_stops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display stops of a bus line."""
        self.message_service.set_bot_instance(context.bot)
        _, line_id, line_name = self.message_service.get_callback_data(update)

        line = await self.bus_service.get_line_by_id(line_id)
        stops = await self.bus_service.get_stops_by_line(line_id)
        encoded = self.mapper.map_bus_stops(stops, line_id, line.ORIGINAL_NOM_LINIA)

        if any(line.alerts):
            line_alerts_url = self.telegraph_service.create_page(f'Bus {line.NOM_LINIA}: Alerts', line.alerts)
            line_alerts_html = f"{self.language_manager.t('common.alerts.line.1')} <a href='{line_alerts_url}'>{self.language_manager.t('common.alerts.line.2')}</a>"

        await self.message_service.send_new_message_from_callback(
            update,
            text=f"{self.language_manager.t('common.line.only.map', line=line_name)}{"\n\n" + line_alerts_html if any(line.alerts) else ''}",
            reply_markup=self.keyboard_factory.map_reply_menu(encoded)
        )

    async def show_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display a specific bus stop with next arrivals."""
        user_id, chat_id, line_id, bus_stop_id = self.message_service.extract_context(update, context)
        logger.info(f"Showing stop info for user {user_id}, line {line_id}, stop {bus_stop_id}")

        default_callback = Callbacks.BUS_STATION.format(line_code=line_id, station_code=bus_stop_id)

        bus_stop = await self.bus_service.get_stop_by_id(bus_stop_id)
        station_alerts = get_alert_by_language(bus_stop, self.user_data_manager.get_user_language(user_id))
        alerts_message = f"{self.language_manager.t("common.alerts")}\n{station_alerts}\n\n" if any(station_alerts) else ""
        
        message = await self.show_stop_intro(update, context, TransportType.BUS.value, line_id, bus_stop_id, bus_stop.NOM_PARADA)
        
        await self.bus_service.get_stop_routes(bus_stop_id)
        await self.update_manager.stop_loading(update, context)

        async def update_text():
            next_buses = await self.bus_service.get_stop_routes(bus_stop_id)
            is_fav = self.user_data_manager.has_favorite(user_id, TransportType.BUS.value, bus_stop_id)
            text = (
                f"{self.language_manager.t(f'{TransportType.BUS.value}.stop.name', name=bus_stop.NOM_PARADA.upper())}\n\n"
                f"{alerts_message}"
                f"<a href='{GoogleMapsHelper.build_directions_url(latitude=bus_stop.coordinates[1], longitude=bus_stop.coordinates[0])}'>{self.language_manager.t('common.map.view.location')}</a>\n\n"
                f"{self.language_manager.t(f'{TransportType.BUS.value}.stop.next')}\n{next_buses.replace('🔜', self.language_manager.t('common.arriving'))}\n\n"
                f"{self.language_manager.t('common.updates.every_x_seconds', seconds=self.UPDATE_INTERVAL)}"
            )
            keyboard = self.keyboard_factory.update_menu(is_fav, TransportType.BUS.value, bus_stop_id, line_id, default_callback, has_connections=False)
            return text, keyboard

        self.start_update_loop(user_id, chat_id, message.message_id, update_text, default_callback)
        logger.info(f"Started update loop task for user {user_id}, station {bus_stop_id}")
