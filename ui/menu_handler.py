import asyncio
from telegram import Update
from telegram.ext import (
    ContextTypes
)

from .keyboard_factory import KeyboardFactory

class MenuHandler:
    def __init__(self, keyboard_factory: KeyboardFactory, message_service, user_data_manager, language_manager, update_manager):
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
            #msg = await self.message_service.send_new_message(update, self.language_manager.t('main.menu.loading'))
            user_id = self.message_service.get_user_id(update)
            self.user_data_manager.register_user(user_id, self.message_service.get_username(update))
            user_language = self.user_data_manager.get_user_language(user_id)
            self.language_manager.set_language(user_language)
            await self.update_manager.stop_loading(update, context)

        msg = await self.message_service.send_new_message(update, self.language_manager.t('main.menu.message'), reply_markup=self.keyboard_factory.create_main_menu_replykeyboard())
        '''
        self.keyboard_factory
        if is_first_message:
            msg = await self.message_service.send_new_message(update, self.language_manager.t('main.menu.loading'), reply_markup=self.keyboard_factory.create_main_menu_replykeyboard())
            user_id = self.message_service.get_user_id(update)
            self.message_service.set_bot_instance(context.bot)
            self.user_data_manager.register_user(self.message_service.get_user_id(update), self.message_service.get_username(update))

            user_language = self.user_data_manager.get_user_language(user_id)
            self.language_manager.set_language(user_language)

            await self.message_service.edit_message_by_id(
                self.message_service.get_chat_id(update),
                msg.message_id,
                self.language_manager.t('main.menu.message'),
                reply_markup=self.keyboard_factory.create_main_menu()
            )

        else:
            await self.message_service.handle_interaction(
                update,
                self.language_manager.t('main.menu.message'),
                reply_markup=self.keyboard_factory.create_main_menu()
            )
        '''
