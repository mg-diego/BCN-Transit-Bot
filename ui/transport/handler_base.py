import asyncio
from collections import defaultdict
import time
import json
from typing import Awaitable, Callable, List
from domain.transport_type import TransportType
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import RetryAfter
from application import MessageService, UpdateManager
from providers.manager.language_manager import LanguageManager
from providers.manager.user_data_manager import UserDataManager
from providers.helpers import logger
from ui.keyboard_factory import KeyboardFactory

class HandlerBase:
    """
    Base class for all transport handlers (Bus, Metro, Tram) with common logic.
    """

    def __init__(self, message_service: MessageService, update_manager: UpdateManager, language_manager: LanguageManager, user_data_manager: UserDataManager, keyboard_factory: KeyboardFactory):
        self.message_service = message_service
        self.update_manager = update_manager
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager
        self.keyboard_factory = keyboard_factory

        self.update_counters = defaultdict(lambda: {"count": 0, "last_reset": time.time()})
        self.ALERT_THRESHOLD = 120  # aviso preventivo
        self.INTERVAL = 60  # segundos
        self.UPDATE_LIMIT = int(self.ALERT_THRESHOLD * 0.8)

        self.UPDATE_INTERVAL = 5


    async def show_transport_lines(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        transport_type: TransportType,
        service_get_lines: Callable[[], Awaitable[List]],
        keyboard_menu_builder: Callable[[List], any]
    ):
        """
        Muestra el menú de líneas de un transporte genérico.
        
        :param transport_type: Enum TransportType (METRO, TRAM, etc.)
        :param service_get_lines: Función async que devuelve la lista de líneas
        :param keyboard_menu_builder: Función que construye el reply_markup con la lista de líneas
        """
        logger.info(f"Showing {transport_type.value.lower()} lines menu")
        type_name = transport_type.value.capitalize()
        
        '''
        # Mensaje de carga
        await self.message_service.send_new_message(
            update,
            self.language_manager.t('common.loading.lines', type=type_name),
            reply_markup=self.keyboard_factory._back_reply_button()
        )
        '''

        await self.update_manager.start_loading(update, context, self.language_manager.t('common.loading.lines', type=type_name), self.keyboard_factory._back_reply_button())
        
        # Obtener líneas
        lines = await service_get_lines()

        await self.update_manager.stop_loading(update, context)
        
        # Construir teclado
        reply_markup = keyboard_menu_builder(lines)
        
        # Enviar menú interactivo
        await self.message_service.handle_interaction(
            update,
            self.language_manager.t('common.select.line', type=type_name),
            reply_markup=reply_markup
        )

    async def ask_search_method(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        transport_type: TransportType
    ):
        """
        Pregunta al usuario cómo quiere buscar una línea: mapa o lista.
        
        :param transport_type: Enum TransportType (METRO, TRAM, etc.)
        """
        _, line_id, line_name = self.message_service.get_callback_data(update)
        self.message_service.set_bot_instance(context.bot)

        logger.info(f"Asking search method map/list for {line_id} ({transport_type.value})")
        
        await self.message_service.edit_inline_message(
            update,
            self.language_manager.t('common.ask.search'),
            reply_markup=self.keyboard_factory.map_or_list_menu(transport_type.value, line_id, line_name)
        )

    async def show_line_stations_list(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        transport_type: TransportType,
        service_get_stations_by_line: Callable[[str], Awaitable[List]],
        keyboard_menu_builder: Callable[[List, str], any]
    ):
        """
        Muestra las estaciones de una línea para cualquier transporte.

        :param transport_type: Enum TransportType
        :param service_get_line_by_id: Función async que devuelve info de la línea
        :param service_get_stations_by_line: Función async que devuelve estaciones de la línea
        :param keyboard_menu_builder: Función que construye el reply_markup con estaciones
        """
        _, line_id, line_name = self.message_service.get_callback_data(update)
        logger.info(f"Showing stations for {transport_type.value.lower()} line {line_id}")

        stations = await service_get_stations_by_line(line_id)
        reply_markup = keyboard_menu_builder(stations, line_id)

        self.message_service.set_bot_instance(context.bot)

        #await self.message_service.send_map_image(update, context, line_name)

        await self.message_service.edit_inline_message(
            update,
            self.language_manager.t("common.line.stops.list", line=line_name),
            reply_markup=reply_markup
        )

    async def show_line_map(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        transport_type: TransportType,
        service_get_stations_by_line: Callable[[str], Awaitable[List]],
        mapper_method: Callable[[List, str, str], str],
        keyboard_menu_builder: Callable[[str], any]
    ):
        """
        Muestra el mapa interactivo de una línea para cualquier transporte.

        :param transport_type: Enum TransportType (METRO, TRAM, BUS, etc.)
        :param service_get_stations_by_line: Función async que devuelve estaciones de la línea
        :param mapper_method: Función que codifica las estaciones en un mapa interactivo
        :param keyboard_menu_builder: Función que construye el reply_markup para el mapa
        """
        _, line_id, line_name = self.message_service.get_callback_data(update)
        logger.info(f"Showing map for {transport_type.value.lower()} line {line_name} (ID: {line_id})")

        stations = await service_get_stations_by_line(line_id)
        encoded_map = mapper_method(stations, line_id, line_name)

        await self.message_service.send_new_message_from_callback(
            update=update,
            text=self.language_manager.t("common.map.open", line_name=line_name),
            reply_markup=keyboard_menu_builder(encoded_map),
        )
    
    async def show_stop_intro(self, update: Update, context, transport_type: str, line_id, stop_id, stop_name):        
        message = await self.update_manager.start_loading(update, context, self.language_manager.t("common.stop.loading"))
        self.user_data_manager.register_search(transport_type, line_id, stop_id, stop_name)

        return message

    def start_update_loop(self, user_id: int, chat_id: int, message_id: int, get_text_callable, previous_callback: str):
        """
        Start an update loop that updates a message periodically.
        - get_text_callable: async function returning the message text.
        - keyboard_callable: function returning reply_markup (optional)
        """       

        async def loop():
            while True:
                try:
                    can_send, send_alert = self.should_send_update(user_id)
                    if can_send:
                        text, reply_markup = await get_text_callable()
                        await self.message_service.edit_message_by_id(chat_id, message_id, text, reply_markup)
                        await asyncio.sleep(5)
                    if send_alert:
                        await self.message_service.edit_message_by_id(chat_id, message_id, self.language_manager.t('common.reload.message'), reply_markup=self.keyboard_factory.restart_search_button(previous_callback))
                        self.reset_user_counter(user_id)
                        break    
                except RetryAfter as e:
                    logger.warning(f"[FloodWait] Waiting {e.retry_after}s for chat {chat_id}: {e}")
                except asyncio.CancelledError:
                    logger.info(f"Update loop cancelled for user {user_id}")
                    break
                except Exception as e:
                    logger.warning(f"Error in update loop for user {user_id}: {e}")
                    break

        self.update_manager.start_task(user_id, loop)

    def should_send_update(self, user_id):
        counter = self.update_counters[user_id]
        now = time.time()

        # Reset del contador cada INTERVAL
        if now - counter["last_reset"] > self.INTERVAL:
            counter["count"] = 0
            counter["last_reset"] = now

        counter["count"] += 1

        # Comprobamos umbral
        if counter["count"] >= self.ALERT_THRESHOLD:
            return False, True  # no enviar update, enviar alerta
        return True, False  # enviar update normalmente
    
    def reset_user_counter(self, user_id):
        self.update_counters[user_id]["count"] = 0
        self.update_counters[user_id]["last_reset"] = time.time()

    
