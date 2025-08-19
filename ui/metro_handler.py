import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory

from application.metro_service import MetroService
from application.update_manager import UpdateManager
from application.message_service import MessageService

from providers.user_data_manager import UserDataManager
from providers.language_manager import LanguageManager

from providers.mapper import Mapper

logger = logging.getLogger(__name__)

class MetroHandler:
    def __init__(
            self,
            keyboard_factory: KeyboardFactory,
            metro_service: MetroService,
            update_manager: UpdateManager,
            user_data_manager: UserDataManager,
            message_service: MessageService,
            language_manager: LanguageManager
        ):
        self.keyboard_factory = keyboard_factory
        self.metro_service = metro_service
        self.update_manager = update_manager
        self.user_data_manager = user_data_manager
        self.message_service = message_service
        self.language_manager = language_manager

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú con todas las líneas de metro."""
        await self.message_service.edit_inline_message(update, self.language_manager.t('metro.loading'))
        metro_lines = await self.metro_service.get_all_lines()
        reply_markup = self.keyboard_factory.metro_lines_menu(metro_lines)
        await self.message_service.edit_inline_message(update, self.language_manager.t('metro.select.line'), reply_markup=reply_markup)

    async def show_line_stations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra las estaciones de una línea."""
        _, line_id = self.message_service.get_callback_data(update)

        line = await self.metro_service.get_line_by_id(line_id)
        stations = await self.metro_service.get_stations_by_line(line_id)
        reply_markup = self.keyboard_factory.metro_stations_menu(stations, line_id)

        await self.message_service.edit_inline_message(update, self.language_manager.t("metro.line.stations", line_id=line.NOM_LINIA), reply_markup=reply_markup)

    async def show_station(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra la información de una estación de una línea."""
        
        self.message_service.set_bot_instance(context.bot)
        user_id = self.message_service.get_user_id(update)
        _, line_id, metro_station_id = self.message_service.get_callback_data(update)

        station = await self.metro_service.get_station_by_id(metro_station_id, line_id)
        station_accesses = await self.metro_service.get_station_accesses(station.CODI_GRUP_ESTACIO)

        await self.message_service.edit_inline_message(update, self.language_manager.t('metro.station.name', station_name=station.NOM_ESTACIO.upper()))

        await self.message_service.send_location(
            update,
            station.coordinates[1],
            station.coordinates[0],
            self.keyboard_factory.metro_station_access_menu(station_accesses)
        )

        message = await self.message_service.send_new_message_from_callback(update, text=self.language_manager.t('metro.station.loading'))
        self.user_data_manager.register_search("metro", line_id, metro_station_id, station.NOM_ESTACIO)
        chat_id = self.message_service.get_chat_id(update)

        station_connections = await self.metro_service.get_metro_station_connections(metro_station_id)
        station_alerts = await self.metro_service.get_metro_station_alerts(line_id, metro_station_id)

        async def update_loop():
            while True:
                try:
                    routes = await self.metro_service.get_station_routes(metro_station_id)

                    text = (
                        f"🚉 {self.language_manager.t('metro.station.next')}\n{routes} \n\n"
                        f"🔛 {self.language_manager.t('metro.station.connections')}\n{station_connections}\n\n"
                        f"🚨 {self.language_manager.t('metro.station.alerts')}\n{station_alerts}"
                    )

                    is_fav = self.user_data_manager.has_favorite(user_id, "metro", metro_station_id)
                    await self.message_service.edit_message_by_id(
                        chat_id,
                        message.message_id,
                        text,
                        reply_markup=self.keyboard_factory.update_menu(is_fav, "metro", metro_station_id, line_id, user_id)
                    )

                    await asyncio.sleep(1)

                except asyncio.CancelledError:
                    logger.info(f"Loop de actualización cancelado para usuario {user_id}")
                    break
                except Exception as e:
                    logger.warning(f"Error actualizando estación: {e}")
                    await self.message_service.edit_message_by_id(
                        chat_id,
                        message.message_id,
                        self.language_manager.t('metro.station.error'),
                        reply_markup=self.keyboard_factory.error_menu(user_id)
                    )
                    break


        self.update_manager.start_task(user_id, update_loop)


    async def close_updates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Detiene la actualización automática de la estación."""

        _, user_id_str = self.message_service.get_callback_data(update)
        user_id = int(user_id_str)

        self.update_manager.cancel_task(user_id)
        await self.message_service.edit_inline_message(update, self.language_manager.t('search.cleaning'))
        await self.message_service.clear_user_messages(user_id)
        await self.message_service.send_new_message_from_callback(update, self.language_manager.t('search.finish'))
        