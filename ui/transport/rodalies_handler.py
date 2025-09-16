from domain.transport_type import TransportType
from telegram import Update
from telegram.ext import ContextTypes

from application import RodaliesService, MessageService, UpdateManager, TelegraphService

from providers.manager import UserDataManager, LanguageManager, audit_action
from providers.helpers import TransportDataCompressor, logger, GoogleMapsHelper

from ui.keyboard_factory import KeyboardFactory
from .handler_base import HandlerBase


class RodaliesHandler(HandlerBase):
    """
    Handles rodalies-related user interactions in the bot.
    """

    def __init__(
        self,
        keyboard_factory: KeyboardFactory,
        rodalies_service: RodaliesService,
        update_manager: UpdateManager,
        user_data_manager: UserDataManager,
        message_service: MessageService,
        language_manager: LanguageManager,
        telegraph_service: TelegraphService
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager, keyboard_factory, telegraph_service)
        self.rodalies_service = rodalies_service
        self.mapper = TransportDataCompressor()
        self.audit_logger = self.user_data_manager.audit_logger

        logger.info(f"[{self.__class__.__name__}] RodaliesHandler initialized")

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_transport_lines(
            update,
            context,
            transport_type=TransportType.RODALIES,
            service_get_lines=self.rodalies_service.get_all_lines,
            keyboard_menu_builder=self.keyboard_factory.rodalies_lines_menu
        )

    @audit_action(action_type="SEARCH", command_or_button="show_rodalies_stops")
    async def show_line_stops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display stations of a rodalies line."""
        self.message_service.set_bot_instance(context.bot)
        _, line_id = self.message_service.get_callback_data(update)

        line = await self.rodalies_service.get_line_by_id(line_id)
        stops = await self.rodalies_service.get_stations_by_line(line_id)
        encoded = self.mapper.map_rodalies_stations(stops, line)

        if line.alerts is not None and any(line.alerts):
            line_alerts_url = self.telegraph_service.create_page(f'{TransportType.RODALIES.value.capitalize()} {line.name}: Alerts', line.alerts)
            line_alerts_html = f"{self.language_manager.t('common.alerts.line.1')} <a href='{line_alerts_url}'>{self.language_manager.t('common.alerts.line.2')}</a>"

        await self.message_service.send_new_message_from_callback(
            update,
            text=f"{self.language_manager.t('common.line.only.map', line=line.name_with_emoji)} {"\n\n" + line_alerts_html if line.alerts is not None and any(line.alerts) else ''}",
            reply_markup=self.keyboard_factory.map_reply_menu(encoded)
        )

    async def show_station(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display a specific rodalies station with next arrivals."""
        user_id, chat_id, line_id, rodalies_station_id = self.message_service.extract_context(update, context)
        logger.info(f"Showing station info for user {user_id}, line {line_id}, stop {rodalies_station_id}")

        default_callback = f"rodalies_station:{line_id}:{rodalies_station_id}"

        rodalies_station = await self.rodalies_service.get_station_by_id(rodalies_station_id, line_id)
        message = await self.show_stop_intro(update, context, TransportType.RODALIES.value, line_id, rodalies_station_id, rodalies_station.name)
        await self.rodalies_service.get_station_routes(rodalies_station_id, line_id)
        await self.update_manager.stop_loading(update, context)
        
        async def update_text():
            next_rodalies = await self.rodalies_service.get_station_routes(rodalies_station_id, line_id)
            next_rodalies = next_rodalies if next_rodalies != '' else self.language_manager.t('no.departures.found')
            is_fav = self.user_data_manager.has_favorite(user_id, TransportType.RODALIES.value, rodalies_station_id)
            text = (
                f"{self.language_manager.t(f'{TransportType.RODALIES.value}.station.name', name=rodalies_station.name.upper())}\n\n"
                f"<a href='{GoogleMapsHelper.build_directions_url(latitude=rodalies_station.latitude, longitude=rodalies_station.longitude, travel_mode='transit')}'>{self.language_manager.t('common.map.view.location')}</a>\n\n"
                f"{self.language_manager.t(f'{TransportType.RODALIES.value}.station.next')}\n{next_rodalies.replace('🔜', self.language_manager.t('common.arriving'))}\n\n"
                f"{self.language_manager.t('common.updates.every_x_seconds', seconds=self.UPDATE_INTERVAL)}"
            ) 
            keyboard = self.keyboard_factory.update_menu(is_fav, TransportType.RODALIES.value, rodalies_station_id, line_id, default_callback, has_connections=False)
            return text, keyboard

        self.start_update_loop(user_id, chat_id, message.message_id, get_text_callable=update_text, previous_callback=default_callback)
        logger.info(f"Started update loop task for user {user_id}, station {rodalies_station_id}")
        