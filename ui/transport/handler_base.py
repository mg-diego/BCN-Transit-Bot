import asyncio
import json
from typing import Awaitable, Callable, List, Tuple, Any
from domain.transport_type import TransportType
from telegram import Update
from telegram.ext import ContextTypes
from application import MessageService, UpdateManager
from providers.manager.language_manager import LanguageManager
from providers.manager.user_data_manager import UserDataManager
from providers.helpers import logger


class HandlerBase:
    """
    Base class for all transport handlers (Bus, Metro, Tram) with common logic.
    """

    def __init__(
        self,
        message_service: MessageService,
        update_manager: UpdateManager,
        language_manager: LanguageManager,
        user_data_manager: UserDataManager
    ):
        self.message_service = message_service
        self.update_manager = update_manager
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager

    async def show_transport_lines(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        transport_type: TransportType,
        service_get_lines: Callable[[], Awaitable[List]],
        keyboard_menu_builder: Callable[[List], Any]
    ):
        """
        Muestra el menú de líneas de un transporte genérico.
        """
        logger.info(f"Showing {transport_type.value.lower()} lines menu")
        type_name = transport_type.value.capitalize()

        # Iniciar animación de carga
        await self.update_manager.start_loading(
            update,
            context,
            self.language_manager.t('common.loading.lines', type=type_name),
            self.keyboard_factory._back_reply_button()
        )

        try:
            # Obtener líneas
            lines = await service_get_lines()

            # Construir teclado
            reply_markup = keyboard_menu_builder(lines)

            # Mostrar menú interactivo
            await self.message_service.handle_interaction(
                update,
                self.language_manager.t('common.select.line', type=type_name),
                reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Failed to load {transport_type.value} lines: {e}")
            await self.message_service.handle_interaction(
                update,
                self.language_manager.t("common.error.loading"),
                reply_markup=self.keyboard_factory._back_reply_button()
            )

        finally:
            # Detener animación en cualquier caso
            await self.update_manager.stop_loading(update, context)

    async def ask_search_method(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        transport_type: TransportType
    ):
        """
        Pregunta al usuario cómo quiere buscar una línea: mapa o lista.
        """
        _, line_id, line_name = self.message_service.get_callback_data(update)
        self.message_service.set_bot_instance(context.bot)

        logger.info(f"Asking search method map/list for {line_id} ({transport_type.value})")

        await self.message_service.edit_inline_message(
            update,
            self.language_manager.t('common.ask.search'),
            reply_markup=self.keyboard_factory.map_or_list_menu(
                transport_type.value,
                line_id,
                line_name
            )
        )

    async def show_line_stations_list(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        transport_type: TransportType,
        service_get_stations_by_line: Callable[[str], Awaitable[List]],
        keyboard_menu_builder: Callable[[List, str], Any]
    ):
        """
        Muestra las estaciones de una línea para cualquier transporte.
        """
        _, line_id, line_name = self.message_service.get_callback_data(update)
        logger.info(f"Showing stations for {transport_type.value.lower()} line {line_id}")

        stations = await service_get_stations_by_line(line_id)
        reply_markup = keyboard_menu_builder(stations, line_id)

        self.message_service.set_bot_instance(context.bot)

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
        keyboard_menu_builder: Callable[[str], Any]
    ):
        """
        Muestra el mapa interactivo de una línea para cualquier transporte.
        """
        _, line_id, line_name = self.message_service.get_callback_data(update)
        logger.info(f"Showing map for {transport_type.value.lower()} line {line_name} (ID: {line_id})")

        stations = await service_get_stations_by_line(line_id)
        encoded_map = mapper_method(stations, line_id, line_name)

        await self.message_service.send_new_message_from_callback(
            update=update,
            text=self.language_manager.t("common.open.map", line_name=line_name),
            reply_markup=keyboard_menu_builder(encoded_map),
        )

    def extract_context(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> Tuple[int, int, str, str]:
        """
        Return common info: user_id, chat_id, line_id, stop_id (if available)
        """
        self.message_service.set_bot_instance(context.bot)
        user_id = self.message_service.get_user_id(update)
        chat_id = self.message_service.get_chat_id(update)

        if update.message and update.message.web_app_data:
            data = json.loads(update.message.web_app_data.data)
            stop_id = data.get("stop_id", "").strip()
            line_id = data.get("line_id", "").strip()
        else:
            callback_data = self.message_service.get_callback_data(update)
            line_id = callback_data[1] if len(callback_data) > 1 else None
            stop_id = callback_data[2] if len(callback_data) > 2 else None

        return user_id, chat_id, line_id, stop_id

    async def show_stop_intro(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        transport_type: str,
        line_id: str,
        stop_id: str,
        stop_lat: float,
        stop_lon: float,
        stop_name: str,
        keyboard_reply=None
    ):
        """
        Muestra info básica de la parada/estación seleccionada + inicia carga.
        """
        sub_key = "station" if transport_type in [
            TransportType.METRO.value,
            TransportType.RODALIES.value
        ] else "stop"

        # Mostrar nombre de la estación/parada
        await self.message_service.handle_interaction(
            update,
            self.language_manager.t(f"{transport_type}.{sub_key}.name", name=stop_name.upper())
        )

        # Enviar ubicación
        await self.message_service.send_location(
            update,
            stop_lat,
            stop_lon,
            reply_markup=keyboard_reply
        )

        # Iniciar animación de carga
        message = await self.update_manager.start_loading(
            update,
            context,
            self.language_manager.t("common.stop.loading")
        )

        # Registrar búsqueda del usuario
        self.user_data_manager.register_search(transport_type, line_id, stop_id, stop_name)

        return message

    def start_update_loop(
        self,
        user_id: int,
        chat_id: int,
        message_id: int,
        get_text_callable: Callable[[], Awaitable[Tuple[str, Any]]]
    ):
        """
        Start an update loop that updates a message periodically.
        """

        async def loop():
            while True:
                try:
                    await asyncio.sleep(1)
                    text, reply_markup = await get_text_callable()
                    await self.message_service.edit_message_by_id(
                        chat_id,
                        message_id,
                        text,
                        reply_markup
                    )
                except asyncio.CancelledError:
                    logger.info(f"Update loop cancelled for user {user_id}")
                    break
                except Exception as e:
                    logger.warning(f"Error in update loop for user {user_id}: {e}")
                    break

        self.update_manager.start_task(user_id, loop)
