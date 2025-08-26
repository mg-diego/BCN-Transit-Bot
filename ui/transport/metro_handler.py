from domain.transport_type import TransportType
from telegram import Update
from telegram.ext import ContextTypes
from providers.helpers import logger

from ui.keyboard_factory import KeyboardFactory

from application import MetroService, UpdateManager, MessageService

from providers.manager import UserDataManager
from providers.manager import LanguageManager
from providers.helpers import TransportDataCompressor

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
        await self.message_service.answer_callback_query(update)
        user_id, chat_id, line_id, metro_station_id = self.extract_context(update, context)        
        logger.info(f"Showing station info for user {user_id}, line {line_id}, station {metro_station_id}")
        station = await self.metro_service.get_station_by_id(metro_station_id)
        message = await self.update_manager.start_loading(update, context, self.language_manager.t('common.stop.loading'))
        is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, metro_station_id)
        
        previous_callback = self.message_service.get_callback_query(update)
        keyboard = self.keyboard_factory.update_menu(is_fav, TransportType.METRO.value, metro_station_id, line_id, user_id, previous_callback)
        await self.show_stop_intro(update, context, transport_type=TransportType.METRO.value, line_id=line_id, stop_id=metro_station_id, stop_name=station.NOM_ESTACIO, stop_lat=station.coordinates[1], stop_lon=station.coordinates[0], keyboard_reply=keyboard)
        
        '''
        routes = await self.metro_service.get_station_routes(metro_station_id)
        station_alerts = await self.metro_service.get_metro_station_alerts(line_id, metro_station_id, self.user_data_manager.get_user_language(user_id))
        alerts_message = f"{self.language_manager.t("common.alerts")}\n{station_alerts}\n\n" if any(station_alerts) else ""

        text = (
            f"{self.language_manager.t(f"metro.station.name", name=station.NOM_ESTACIO.upper())}\n\n"
            f"🚉 {self.language_manager.t('metro.station.next')}\n{routes} \n\n"
            f"{alerts_message}"
        )
        is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, metro_station_id)
        message = await self.message_service.handle_interaction(
            update,
            text,
            reply_markup=self.keyboard_factory.update_menu(is_fav, TransportType.METRO.value, metro_station_id, line_id, user_id, self.message_service.get_callback_query(update))
        )    
        '''
        
        station_alerts = await self.metro_service.get_metro_station_alerts(line_id, metro_station_id, self.user_data_manager.get_user_language(user_id))     
        alerts_message = f"{self.language_manager.t("common.alerts")}\n{station_alerts}\n\n" if any(station_alerts) else ""

        async def update_text():
            routes = await self.metro_service.get_station_routes(metro_station_id)       

            text = (
                f"{self.language_manager.t(f"metro.station.name", name=station.NOM_ESTACIO.upper())}\n\n"
                f"🚉 {self.language_manager.t('metro.station.next')}\n{routes} \n\n"
                f"{alerts_message}"
            )
            is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, metro_station_id)
            keyboard = self.keyboard_factory.update_menu(is_fav, TransportType.METRO.value, metro_station_id, line_id, user_id, previous_callback)
            return text, keyboard
        
        await update_text()
        self.start_update_loop(user_id, update, update_text)
        logger.info(f"Started update loop task for user {user_id}, station {metro_station_id}")

    async def show_station_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.message_service.get_chat_id(update)
        self.message_service.set_bot_instance(context.bot)

        # 1. Cancelar cualquier actualización en curso (parar el loop de tiempos)
        self.update_manager.cancel_task(user_id)
        logger.info(f"[MetroHandler] Update task cancelled for user {user_id} to show station accesses")

        # 2. Obtener datos necesarios de la callback
        _, line_id, station_id = self.message_service.get_callback_data(update)
        station = await self.metro_service.get_station_by_id(station_id)        
        station_accesses = await self.metro_service.get_station_accesses(station.CODI_GRUP_ESTACIO)
        logger.info(f"[MetroHandler] Showing accesses for station ID: {station_id}")

        access_text = ''
        for access in station_accesses:
            access_text += f" - {"🛗" if access.NUM_ASCENSORS > 0 else "🚶‍♂️"} <a href='https://maps.google.com/?q={access.coordinates[1]},{access.coordinates[0]}'>{access.NOM_ACCES}</a>\n" 

        print(access_text)
        text = (
            f"{self.language_manager.t(f"metro.station.name", name=station.NOM_ESTACIO.upper())}\n\n"
            f"<b><u>Accesos</u></b>\n{access_text} \n\n"
        )

        is_fav = self.user_data_manager.has_favorite(user_id, TransportType.METRO.value, station_id)

        # 5. Mostrar información estática
        await self.message_service.edit_inline_message(
            update,
            text,
            reply_markup=self.keyboard_factory.update_menu(is_fav, "metro", station_id, line_id, user_id, self.message_service.get_callback_query(update))
        )

    async def show_station_connections(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass
