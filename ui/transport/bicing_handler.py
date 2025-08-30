from telegram import Update
from telegram.ext import ContextTypes
from domain.transport_type import TransportType
from providers.helpers.google_maps_helper import GoogleMapsHelper
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

    async def show_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.message_service.set_bot_instance(context.bot)

        await self.message_service.send_new_message(update, self.language_manager.t('bicing.search.instructions'), reply_markup=self.keyboard_factory.location_keyboard())

        # PENDING TO FIX MAP VIEW
        '''
        stations = await self.bicing_service.get_all_stations()
        encoded = self.mapper.map_bicing_stations(stations)

        await self.message_service.send_new_message_from_callback(
            update,
            text=self.language_manager.t('common.line.only.map', line=''),
            reply_markup=self.keyboard_factory.map_reply_menu(encoded)
        )
        '''

    async def show_station(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id, chat_id, line_id, bicing_station_id = self.message_service.extract_context(update, context)
        logger.info(f"Showing bicing station info for user {user_id}, station {bicing_station_id}")

        default_callback = f"bicing_station:{bicing_station_id}"

        station = await self.bicing_service.get_station_by_id(bicing_station_id)
        message = await self.show_stop_intro(update, context, TransportType.BICING.value, '', bicing_station_id, station.streetName)
        await self.update_manager.stop_loading(update, context)

        async def update_text():
            station = await self.bicing_service.get_station_by_id(bicing_station_id)
            text = (
                f"{self.language_manager.t(f'{TransportType.BICING.value}.station.name', station_id=station.id)}\n\n"
                f"<a href='{GoogleMapsHelper.build_directions_url(latitude=station.latitude, longitude=station.longitude)}'>📍{station.streetName}</a>\n\n"
                f"{self.language_manager.t(
                    f'{TransportType.BICING.value}.station.details',
                    slots=station.slots,
                    available_bikes=station.bikes,
                    electrical_bikes=station.electrical_bikes,
                    mechanical_bikes=station.mechanical_bikes,
                    availability=station.disponibilidad,
                    status= '✅' if station.status == 1 else '❌'
                )}\n\n"
                f"{self.language_manager.t('common.updates.every_x_seconds', seconds=self.UPDATE_INTERVAL)}\n\n"
            )
            is_fav = self.user_data_manager.has_favorite(user_id, TransportType.BICING.value, bicing_station_id)
            keyboard = self.keyboard_factory.update_menu(is_fav, TransportType.BICING.value, bicing_station_id, '', default_callback, has_connections=False)
            return text, keyboard
        
        self.start_update_loop(user_id, chat_id, message.message_id, update_text, default_callback)
        logger.info(f"Started update loop task for user {user_id}, bicing station {bicing_station_id}")