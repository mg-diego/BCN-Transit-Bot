from domain.transport_type import TransportType
from domain.metro import get_alert_by_language, format_metro_connections
from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory

from application import MetroService, UpdateManager, MessageService, TelegraphService

from providers.manager import LanguageManager, UserDataManager, audit_action
from providers.helpers import TransportDataCompressor, GoogleMapsHelper, logger

from .handler_base import HandlerBase

class MetroHandler(HandlerBase):
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
        self.audit_logger = self.user_data_manager.audit_logger
        logger.info(f"[{self.__class__.__name__}] MetroHandler initialized")

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_transport_lines(
            update,
            context,
            transport_type=TransportType.METRO,
            service_get_lines=self.metro_service.get_all_lines,
            keyboard_menu_builder=self.keyboard_factory.metro_lines_menu
        )

    async def ask_search_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _, line_id, line_name = self.message_service.get_callback_data(update)
        line = await self.metro_service.get_line_by_id(line_id)
        await super().ask_search_method(update, context, transport_type=TransportType.METRO, alerts=line.alerts)

    async def show_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_line_stations_list(
            update,
            context,
            transport_type=TransportType.METRO,
            service_get_stations_by_line=self.metro_service.get_stations_by_line,
            keyboard_menu_builder=self.keyboard_factory.metro_stations_menu
        )

    async def show_map(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_line_map(
            update,
            context,
            transport_type=TransportType.METRO,
            service_get_stations_by_line=self.metro_service.get_stations_by_line,
            mapper_method=self.mapper.map_metro_stations,
            keyboard_menu_builder=self.keyboard_factory.map_reply_menu
        )

    async def show_station(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id, chat_id, line_id, metro_station_id = self.message_service.extract_context(update, context)        
        logger.info(f"Showing metro station info for user {user_id}, line {line_id}, station {metro_station_id}")
        
        default_callback = f"metro_station:{line_id}:{metro_station_id}"
        callback = self.message_service.get_callback_query(update)
        callback = 'metro_station' if callback is None else callback

        station = await self.metro_service.get_station_by_id(metro_station_id)

        message = await self.show_stop_intro(update, context, TransportType.METRO.value, line_id, metro_station_id, station.name)

        await self.metro_service.get_station_routes(metro_station_id)
        station_alerts = get_alert_by_language(station, self.user_data_manager.get_user_language(user_id))
        alerts_message = f"{self.language_manager.t("common.alerts")}\n{station_alerts}\n\n" if any(station_alerts) else ""

        await self.update_manager.stop_loading(update, context)

        async def update_text():
            routes = await self.metro_service.get_station_routes(metro_station_id)
            text = (
                f"{self.language_manager.t(f'{TransportType.METRO.value}.station.name', name=station.name.upper())}\n\n"
                f"{alerts_message}"
                f"<a href='{GoogleMapsHelper.build_directions_url(latitude=station.latitude, longitude=station.longitude)}'>{self.language_manager.t('common.map.view.location')}</a>\n\n"
                f"{self.language_manager.t(f'{TransportType.METRO.value}.station.next')}\n{routes.replace('🔜', self.language_manager.t('common.arriving'))}\n\n"
                f"{self.language_manager.t('common.updates.every_x_seconds', seconds=self.UPDATE_INTERVAL)}"
            )
            is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, metro_station_id)
            keyboard = self.keyboard_factory.update_menu(is_fav, TransportType.METRO.value, metro_station_id, line_id, callback, has_connections=any(station.connections))
            return text, keyboard

        self.start_update_loop(user_id, chat_id, message.message_id, update_text, default_callback)
        logger.info(f"Started update loop task for user {user_id}, station {metro_station_id}")

    @audit_action(action_type="SEARCH", command_or_button="show_station_access")
    async def show_station_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.message_service.get_chat_id(update)
        self.message_service.set_bot_instance(context.bot)

        # 1. Cancelar cualquier actualización en curso (parar el loop de tiempos)
        self.update_manager.cancel_task(user_id)
        logger.info(f"[MetroHandler] Update task cancelled for user {user_id} to show station accesses")

        # 2. Obtener datos necesarios de la callback
        _, line_id, station_id = self.message_service.get_callback_data(update)
        station = await self.metro_service.get_station_by_id(station_id)        
        station_accesses = await self.metro_service.get_station_accesses(station.CODI_GRUP_ESTACIO)
        station_alerts = get_alert_by_language(station, self.user_data_manager.get_user_language(user_id))
        alerts_message = f"{self.language_manager.t("common.alerts")}\n{station_alerts}\n\n" if any(station_alerts) else ""
        logger.info(f"[MetroHandler] Showing accesses for station ID: {station_id}")

        access_text = ''
        for access in station_accesses:
            access_text += f" - {"🛗" if access.NUM_ASCENSORS > 0 else "🚶‍♂️"} <a href='{GoogleMapsHelper.build_directions_url(latitude=access.coordinates[1], longitude=access.coordinates[0])}'>{access.NOM_ACCES}</a>\n" 

        text = (
            f"{self.language_manager.t(f"metro.station.name", name=station.name.upper())}\n\n"
            f"{alerts_message}"
            f"<a href='{GoogleMapsHelper.build_directions_url(latitude=station.latitude, longitude=station.longitude)}'>{self.language_manager.t('common.map.view.location')}</a>\n\n"
            f"<b><u>Accesos</u></b>\n{access_text} \n\n"
        )

        is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, station_id)

        # 5. Mostrar información estática
        await self.message_service.edit_inline_message(
            update,
            text,
            reply_markup=self.keyboard_factory.update_menu(is_fav, TransportType.METRO.value, station_id, line_id, self.message_service.get_callback_query(update), has_connections=any(station.connections))
        )

    @audit_action(action_type="SEARCH", command_or_button="show_station_connections")
    async def show_station_connections(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.message_service.get_chat_id(update)
        self.message_service.set_bot_instance(context.bot)

        # 1. Cancelar cualquier actualización en curso (parar el loop de tiempos)
        self.update_manager.cancel_task(user_id)
        logger.info(f"[MetroHandler] Update task cancelled for user {user_id} to show station accesses")

        # 2. Obtener datos necesarios de la callback
        _, line_id, station_id = self.message_service.get_callback_data(update)
        station = await self.metro_service.get_station_by_id(station_id)        
        station_connections = format_metro_connections(station.connections)
        station_alerts = get_alert_by_language(station, self.user_data_manager.get_user_language(user_id))
        alerts_message = f"{self.language_manager.t("common.alerts")}\n{station_alerts}\n\n" if any(station_alerts) else ""
        logger.info(f"[MetroHandler] Showing connections for station ID: {station_id}")

        text = (
            f"{self.language_manager.t(f"metro.station.name", name=station.name.upper())}\n\n"
            f"{alerts_message}"
            f"<a href='{GoogleMapsHelper.build_directions_url(latitude=station.latitude, longitude=station.longitude)}'>{self.language_manager.t('common.map.view.location')}</a>\n\n"
            f"<b><u>Connections</u></b>\n{station_connections} \n\n"
        )

        is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, station_id)

        # 5. Mostrar información estática
        await self.message_service.edit_inline_message(
            update,
            text,
            reply_markup=self.keyboard_factory.update_menu(is_fav, TransportType.METRO.value, station_id, line_id, self.message_service.get_callback_query(update), has_connections=False)
        )
