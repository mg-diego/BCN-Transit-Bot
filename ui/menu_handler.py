from telegram import Update
from telegram.ext import (
    ContextTypes
)
from application import MessageService, UpdateManager
from providers.helpers import logger
from providers.manager import UserDataManager, LanguageManager

from .keyboard_factory import KeyboardFactory

class MenuHandler:
    def __init__(self, keyboard_factory: KeyboardFactory, message_service: MessageService, user_data_manager: UserDataManager, language_manager: LanguageManager, update_manager: UpdateManager):
        self.keyboard_factory = keyboard_factory
        self.message_service = message_service
        self.user_data_manager = user_data_manager
        self.language_manager = language_manager
        self.update_manager = update_manager

    async def back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_menu(update, context, False)

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, is_first_message = True):
        if is_first_message:
            await self.update_manager.start_loading(update, context, base_text=self.language_manager.t('main.menu.loading'))
            user_id = self.message_service.get_user_id(update)
            self.user_data_manager.register_user(user_id, self.message_service.get_username(update))
            user_language = self.user_data_manager.get_user_language(user_id)
            self.language_manager.set_language(user_language)
            await self.update_manager.stop_loading(update, context)

        msg = await self.message_service.send_message_direct(self.message_service.get_chat_id(update), context, self.language_manager.t('main.menu.message'), reply_markup=self.keyboard_factory.create_main_menu_replykeyboard())
            

    async def close_updates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        _, user_id_str = self.message_service.get_callback_data(update)
        user_id = int(user_id_str)
        logger.info(f"Stopping updates for user {user_id}")

        self.update_manager.cancel_task(user_id)
        await self.message_service.edit_inline_message(update, self.language_manager.t('search.cleaning'))
        await self.message_service.clear_user_messages(user_id)
        logger.info(f"Updates stopped and messages cleared for user {user_id}")
        await self.back_to_menu(update, context)
