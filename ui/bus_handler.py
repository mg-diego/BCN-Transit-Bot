import asyncio
import logging
import json
from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory

from application.bus_service import BusService
from application.update_manager import UpdateManager
from application.message_service import MessageService

from providers.user_data_manager import UserDataManager
from providers.language_manager import LanguageManager

from providers.mapper import Mapper

logger = logging.getLogger(__name__)

class BusHandler:
    def __init__(
            self,
            keyboard_factory: KeyboardFactory,
            bus_service: BusService,
            update_manager: UpdateManager,
            user_data_manager: UserDataManager,
            message_service: MessageService,
            language_manager: LanguageManager
        ):
        self.keyboard_factory = keyboard_factory
        self.bus_service = bus_service
        self.update_manager = update_manager
        self.user_data_manager = user_data_manager
        self.message_service = message_service
        self.language_manager = language_manager

        self.mapper = Mapper()

    async def show_lines(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú con todas las líneas de bus."""
        await self.message_service.edit_inline_message(update, self.language_manager.t("bus.loading"))
        bus_lines = await self.bus_service.get_all_lines()
        reply_markup = self.keyboard_factory.bus_lines_menu(bus_lines)
        await self.message_service.edit_inline_message(update, self.language_manager.t("bus.select.line"), reply_markup=reply_markup)

    async def show_line_stops(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra las paradas de una línea."""
        self.message_service.set_bot_instance(context.bot)
        _, line_id, line_name = self.message_service.get_callback_data(update)

        stops = await self.bus_service.get_stops_by_line(line_id)
        encoded = self.mapper.map_bus_stops(stops, line_id)
        print(encoded)

        await self.message_service.send_new_message_from_callback(
            update = update,
            text = self.language_manager.t('bus.line.stops', line_name=line_name),
            reply_markup = self.keyboard_factory.bus_stops_map_menu(encoded),
        )

    async def show_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message and update.message.web_app_data:
            data_str = update.message.web_app_data.data
            data = json.loads(data_str)
            bus_stop_id = data.get("name").split("-")[0].strip()
            line_id = data.get("line_id").strip()
        else:                
            _, line_id, bus_stop_id = self.message_service.get_callback_data(update)

        user_id = self.message_service.get_user_id(update)
        chat_id = self.message_service.get_chat_id(update)
        bus_stop = await self.bus_service.get_stop_by_id(bus_stop_id, line_id)
        
        await self.message_service.handle_interaction(update, self.language_manager.t('bus.stop.name', bus_stop_name=bus_stop.NOM_PARADA.upper()))

        await self.message_service.send_location(
            update,
            bus_stop.coordinates[1],
            bus_stop.coordinates[0]
        )

        # Primer mensaje
        message = await self.message_service.send_new_message_from_callback(update, text=self.language_manager.t('bus.stop.loading'))
        self.user_data_manager.register_search("bus", line_id, bus_stop_id, bus_stop.NOM_PARADA)
        
        async def update_loop():
            while True:
                try:
                    next_buses = await self.bus_service.get_stop_routes(bus_stop_id)

                    text = (
                        f"🚉 {self.language_manager.t('bus.stop.next')}\n{next_buses}"
                    )

                    is_fav = self.user_data_manager.has_favorite(user_id, "bus", bus_stop_id)

                    await self.message_service.edit_message_by_id(
                        chat_id,
                        message.message_id,
                        text,
                        reply_markup=self.keyboard_factory.update_menu(is_fav, "bus", bus_stop_id, line_id, user_id)
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
                        self.language_manager.t('bus.stop.error'),
                        reply_markup=self.keyboard_factory.error_menu(user_id)
                    )
                    break

        self.update_manager.start_task(user_id, update_loop)