from domain.common.line_route import LineRoute
from domain.transport_type import TransportType
from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory

from application import FgcService, UpdateManager, MessageService, TelegraphService

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
        fgc_service: FgcService,
        update_manager: UpdateManager,
        user_data_manager: UserDataManager,
        message_service: MessageService,
        language_manager: LanguageManager,
        telegraph_service: TelegraphService
    ):
        super().__init__(message_service, update_manager, language_manager, user_data_manager, keyboard_factory, telegraph_service)
        self.fgc_service = fgc_service
        self.mapper = TransportDataCompressor()
        logger.info(f"[{self.__class__.__name__}] FgcHandler initialized")


    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_transport_lines(
            update,
            context,
            transport_type=TransportType.FGC,
            service_get_lines=self.fgc_service.get_all_lines,
            keyboard_menu_builder=self.keyboard_factory.fgc_lines_menu
        )

    async def ask_search_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await super().ask_search_method(update, context, transport_type=TransportType.FGC)
    
    async def show_map(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display stations of a rodalies line."""
        self.message_service.set_bot_instance(context.bot)
        _, line_id, line_name = self.message_service.get_callback_data(update)

        line = await self.fgc_service.get_line_by_id(line_id)
        stations = await self.fgc_service.get_stations_by_line(line_id)
        encoded = self.mapper.map_fgc_stations(stations, line)

        await self.message_service.send_new_message_from_callback(
            update=update,
            text=self.language_manager.t("common.map.open", line_name=line_name),
            reply_markup=self.keyboard_factory.map_reply_menu(encoded),
        )

    async def show_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_line_stations_list(
            update,
            context,
            transport_type=TransportType.FGC,
            service_get_stations_by_line=self.fgc_service.get_stations_by_line,
            keyboard_menu_builder=self.keyboard_factory.fgc_stations_menu
        )

    async def show_station(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id, chat_id, line_id, fgc_station_id = self.message_service.extract_context(update, context)
        logger.info(f"Showing station info for user {user_id}, line {line_id}, stop {fgc_station_id}")

        default_callback = f"fgc_station:{line_id}:{fgc_station_id}"

        fgc_station = await self.fgc_service.get_station_by_id(fgc_station_id, line_id)
        message = await self.show_stop_intro(update, context, TransportType.FGC.value, line_id, fgc_station_id, fgc_station.name)
        await self.fgc_service.get_station_routes(fgc_station.code)
        await self.update_manager.stop_loading(update, context)
        
        async def update_text():
            next_fgc = "\n\n".join(LineRoute.scheduled_list(route) for route in await self.fgc_service.get_station_routes(fgc_station.code) if route.line_id == line_id)
            next_fgc = next_fgc if next_fgc != '' else self.language_manager.t('no.departures.found')
            is_fav = await self.user_data_manager.has_favorite(user_id, TransportType.FGC.value, fgc_station_id)
            text = (
                f"{self.language_manager.t(f'{TransportType.FGC.value}.station.name', name=fgc_station.name.upper())}\n\n"
                f"<a href='{GoogleMapsHelper.build_directions_url(latitude=fgc_station.latitude, longitude=fgc_station.longitude, travel_mode='transit')}'>{self.language_manager.t('common.map.view.location')}</a>\n\n"
                f"{self.language_manager.t(f'{TransportType.FGC.value}.station.next')}\n{next_fgc.replace('🔜', self.language_manager.t('common.arriving'))}\n\n"
                f"{self.language_manager.t('common.updates.every_x_seconds', seconds=self.UPDATE_INTERVAL)}"
            ) 
            keyboard = self.keyboard_factory.update_menu(is_fav, TransportType.FGC.value, fgc_station_id, line_id, default_callback, has_connections=False)
            return text, keyboard

        self.start_update_loop(user_id, chat_id, message.message_id, get_text_callable=update_text, previous_callback=default_callback)
        logger.info(f"Started update loop task for user {user_id}, station {fgc_station_id}")

