import asyncio
import json
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

    def __init__(self, message_service: MessageService, update_manager: UpdateManager, language_manager: LanguageManager, user_data_manager: UserDataManager):
        self.message_service = message_service
        self.update_manager = update_manager
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager

    def extract_context(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Return common info: user_id, chat_id, line_id, stop_id (if available)"""
        self.message_service.set_bot_instance(context.bot)
        user_id = self.message_service.get_user_id(update)
        chat_id = self.message_service.get_chat_id(update)

        if update.message and update.message.web_app_data:
            data = json.loads(update.message.web_app_data.data)
            stop_id = data.get("stop_id").strip()
            line_id = data.get("line_id").strip()
        else:
            callback_data = self.message_service.get_callback_data(update)
            line_id = callback_data[1] if len(callback_data) > 1 else None
            stop_id = callback_data[2] if len(callback_data) > 2 else None

        return user_id, chat_id, line_id, stop_id
    
    async def show_stop_intro(self, update: Update, transport_type: str, line_id, stop_id, stop_lat, stop_lon, stop_name, keyboard_reply = None):
        sub_key = "station" if transport_type in [TransportType.METRO.value, TransportType.RODALIES.value] else "stop"
        await self.message_service.handle_interaction(update, self.language_manager.t(f"{transport_type}.{sub_key}.name", name=stop_name.upper()))
        await self.message_service.send_location(update, stop_lat, stop_lon, reply_markup=keyboard_reply)

        message = await self.message_service.send_new_message_from_callback(update, text=self.language_manager.t("common.stop.loading"))

        self.user_data_manager.register_search(transport_type, line_id, stop_id, stop_name)

        return message

    def start_update_loop(self, user_id: int, chat_id: int, message_id: int, get_text_callable):
        """
        Start an update loop that updates a message periodically.
        - get_text_callable: async function returning the message text.
        - keyboard_callable: function returning reply_markup (optional)
        """

        async def loop():
            while True:
                try:
                    text, reply_markup = await get_text_callable()
                    await self.message_service.edit_message_by_id(chat_id, message_id, text, reply_markup)
                    await asyncio.sleep(1)
                except asyncio.CancelledError:
                    logger.info(f"Update loop cancelled for user {user_id}")
                    break
                except Exception as e:
                    logger.warning(f"Error in update loop for user {user_id}: {e}")
                    break

        self.update_manager.start_task(user_id, loop)

    
