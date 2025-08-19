import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory

from application.tram_service import TramService
from application.update_manager import UpdateManager
from application.message_service import MessageService

from providers.user_data_manager import UserDataManager
from providers.language_manager import LanguageManager

logger = logging.getLogger(__name__)

class TramHandler:
    def __init__(
            self,
            keyboard_factory: KeyboardFactory,
            tram_service: TramService,
            update_manager: UpdateManager,
            user_data_manager: UserDataManager,
            message_service: MessageService,
            language_manager: LanguageManager
        ):
        self.keyboard_factory = keyboard_factory
        self.tram_service = tram_service
        self.update_manager = update_manager
        self.user_data_manager = user_data_manager
        self.message_service = message_service
        self.language_manager = language_manager

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú con todas las líneas de tram."""
        await self.message_service.edit_inline_message(update, self.language_manager.t('tram.loading'))
        tram_lines = await self.tram_service.get_all_lines()
        reply_markup = self.keyboard_factory.tram_lines_menu(tram_lines)
        await self.message_service.edit_inline_message(update, self.language_manager.t('tram.select.line'), reply_markup=reply_markup)


    async def show_line_stops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra las paradas de una línea."""
        _, line_id, line_name = self.message_service.get_callback_data(update)

        #line = await self.tram_service.get_line_by_id(line_id)
        stops = await self.tram_service.get_stops_by_line(line_id)
        reply_markup = self.keyboard_factory.tram_stops_menu(stops, line_id)

        await self.message_service.edit_inline_message(update, self.language_manager.t("tram.line.stops", line_id=line_name), reply_markup=reply_markup)


    async def show_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra la información de una parada de una línea."""
        
        self.message_service.set_bot_instance(context.bot)
        user_id = self.message_service.get_user_id(update)
        _, line_id, stop_id = self.message_service.get_callback_data(update)

        stop = await self.tram_service.get_stop_by_id(stop_id, line_id)

        await self.message_service.edit_inline_message(update, self.language_manager.t('tram.stop.name', tram_stop_name=stop.name.upper()))

        await self.message_service.send_location(
            update,
            stop.latitude,
            stop.longitude,
        )

        message = await self.message_service.send_new_message_from_callback(update, text=self.language_manager.t('tram.stop.loading'))
        
        self.user_data_manager.register_search("tram", line_id, stop_id, stop.name)
        
        chat_id = self.message_service.get_chat_id(update)

        
        stop_connections = await self.tram_service.get_tram_stop_connections(stop_id)        
        stop_alerts =  "" #await self.metro_service.get_metro_station_alerts(line_id, metro_station_id)
        
        async def update_loop():
            while True:
                try:
                    routes = await self.tram_service.get_stop_routes(stop.outboundCode, stop.returnCode)

                    text = (
                        f"🚉 {self.language_manager.t('tram.stop.next')}\n{routes} \n\n"
                        f"🔛 {self.language_manager.t('tram.stop.connections')}\n{stop_connections}\n\n"
                        f"🚨 {self.language_manager.t('tram.stop.alerts')}\n{stop_alerts}"
                    )

                    is_fav = self.user_data_manager.has_favorite(user_id, "tram", stop_id)
                    await self.message_service.edit_message_by_id(
                        chat_id,
                        message.message_id,
                        text,
                        reply_markup=self.keyboard_factory.update_menu(is_fav, "tram", stop_id, line_id, user_id)
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
                        self.language_manager.t('tram.stop.error'),
                        reply_markup=self.keyboard_factory.error_menu(user_id)
                    )
                    break

        self.update_manager.start_task(user_id, update_loop)
        
