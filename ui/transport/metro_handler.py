from domain.transport_type import TransportType
from domain.metro import get_alert_by_language
from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory

from application import MetroService, UpdateManager, MessageService

from providers.manager import UserDataManager
from providers.manager import LanguageManager
from providers.helpers import TransportDataCompressor, GoogleMapsHelper, logger, BoolConverter

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
        language_manager: LanguageManager
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager, keyboard_factory)
        self.metro_service = metro_service
        self.mapper = TransportDataCompressor()
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
        await super().ask_search_method(update, context, transport_type=TransportType.METRO)

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
            keyboard_menu_builder=self.keyboard_factory.bus_stops_map_menu
        )

    async def show_station(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id, chat_id, line_id, metro_station_id = self.message_service.extract_context(update, context)        
        logger.info(f"Showing station info for user {user_id}, line {line_id}, station {metro_station_id}")
        
        default_callback = f"metro_station:{line_id}:{metro_station_id}"
        callback = self.message_service.get_callback_query(update)
        callback = 'metro_station' if callback is None else callback

        station = await self.metro_service.get_station_by_id(metro_station_id)

        message = await self.show_stop_intro(update, context, TransportType.METRO.value, line_id, metro_station_id, station.NOM_ESTACIO)

        await self.metro_service.get_station_routes(metro_station_id)
        station_connections = await self.metro_service.get_station_connections(metro_station_id)
        station_alerts = get_alert_by_language(station, self.user_data_manager.get_user_language(user_id))
        alerts_message = f"{self.language_manager.t("common.alerts")}\n{station_alerts}\n\n" if any(station_alerts) else ""

        await self.update_manager.stop_loading(update, context)

        async def update_text():
            routes = await self.metro_service.get_station_routes(metro_station_id)
            text = (
                f"{self.language_manager.t(f'{TransportType.METRO.value}.station.name', name=station.NOM_ESTACIO.upper())}\n\n"
                f"{alerts_message}"
                f"<a href='{GoogleMapsHelper.build_directions_url(latitude=station.coordinates[1], longitude=station.coordinates[0])}'>{self.language_manager.t('common.map.view.location')}</a>\n\n"
                f"{self.language_manager.t(f'{TransportType.METRO.value}.station.next')}\n{routes.replace('🔜', self.language_manager.t('common.arriving'))}\n\n"
                f"{self.language_manager.t('common.updates.every_x_seconds', seconds=self.UPDATE_INTERVAL)}"
            )
            is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, metro_station_id)
            keyboard = self.keyboard_factory.update_menu(is_fav, TransportType.METRO.value, metro_station_id, line_id, callback, has_connections=any(station_connections))
            return text, keyboard

        self.start_update_loop(user_id, chat_id, message.message_id, update_text, default_callback)
        logger.info(f"Started update loop task for user {user_id}, station {metro_station_id}")

    async def show_station_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.message_service.get_chat_id(update)
        self.message_service.set_bot_instance(context.bot)

        # 1. Cancelar cualquier actualización en curso (parar el loop de tiempos)
        self.update_manager.cancel_task(user_id)
        logger.info(f"[MetroHandler] Update task cancelled for user {user_id} to show station accesses")

        # 2. Obtener datos necesarios de la callback
        _, line_id, station_id, has_connections = self.message_service.get_callback_data(update)
        station = await self.metro_service.get_station_by_id(station_id)        
        station_accesses = await self.metro_service.get_station_accesses(station.CODI_GRUP_ESTACIO)
        station_alerts = get_alert_by_language(station, self.user_data_manager.get_user_language(user_id))
        alerts_message = f"{self.language_manager.t("common.alerts")}\n{station_alerts}\n\n" if any(station_alerts) else ""
        logger.info(f"[MetroHandler] Showing accesses for station ID: {station_id}")

        access_text = ''
        for access in station_accesses:
            access_text += f" - {"🛗" if access.NUM_ASCENSORS > 0 else "🚶‍♂️"} <a href='{GoogleMapsHelper.build_directions_url(latitude=access.coordinates[1], longitude=access.coordinates[0])}'>{access.NOM_ACCES}</a>\n" 

        text = (
            f"{self.language_manager.t(f"metro.station.name", name=station.NOM_ESTACIO.upper())}\n\n"
            f"{alerts_message}"
            f"<a href='{GoogleMapsHelper.build_directions_url(latitude=station.coordinates[1], longitude=station.coordinates[0])}'>{self.language_manager.t('common.map.view.location')}</a>\n\n"
            f"<b><u>Accesos</u></b>\n{access_text} \n\n"
        )

        is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, station_id)

        # 5. Mostrar información estática
        await self.message_service.edit_inline_message(
            update,
            text,
            reply_markup=self.keyboard_factory.update_menu(is_fav, TransportType.METRO.value, station_id, line_id, self.message_service.get_callback_query(update), has_connections=BoolConverter.from_string(has_connections))
        )

    async def show_station_connections(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.message_service.get_chat_id(update)
        self.message_service.set_bot_instance(context.bot)

        # 1. Cancelar cualquier actualización en curso (parar el loop de tiempos)
        self.update_manager.cancel_task(user_id)
        logger.info(f"[MetroHandler] Update task cancelled for user {user_id} to show station accesses")

        # 2. Obtener datos necesarios de la callback
        _, line_id, station_id, has_connections = self.message_service.get_callback_data(update)
        station = await self.metro_service.get_station_by_id(station_id)        
        station_connections = await self.metro_service.get_station_connections(station.ID_ESTACIO)
        station_alerts = get_alert_by_language(station, self.user_data_manager.get_user_language(user_id))
        alerts_message = f"{self.language_manager.t("common.alerts")}\n{station_alerts}\n\n" if any(station_alerts) else ""
        logger.info(f"[MetroHandler] Showing connections for station ID: {station_id}")

        text = (
            f"{self.language_manager.t(f"metro.station.name", name=station.NOM_ESTACIO.upper())}\n\n"
            f"{alerts_message}"
            f"<a href='{GoogleMapsHelper.build_directions_url(latitude=station.coordinates[1], longitude=station.coordinates[0])}'>{self.language_manager.t('common.map.view.location')}</a>\n\n"
            f"<b><u>Connections</u></b>\n{station_connections} \n\n"
        )

        is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, station_id)

        # 5. Mostrar información estática
        await self.message_service.edit_inline_message(
            update,
            text,
            reply_markup=self.keyboard_factory.update_menu(is_fav, TransportType.METRO.value, station_id, line_id, self.message_service.get_callback_query(update), has_connections=BoolConverter.from_string(has_connections))
        )
