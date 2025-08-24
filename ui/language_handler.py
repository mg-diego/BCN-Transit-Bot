import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class LanguageHandler:
    def __init__(self, keyboard_factory, user_data_manager, message_service, language_manager):
        self.keyboard_factory = keyboard_factory
        self.user_data_manager = user_data_manager
        self.message_service = message_service
        self.language_manager = language_manager

    async def show_languages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.message_service.get_user_id(update)
        current_language = self.user_data_manager.get_user_language(user_id)
        available_languages = self.language_manager.get_available_languages()

        user_available_new_languages = {}
        for language in available_languages:
            if language != current_language:
                user_available_new_languages[language] = self.language_manager.t(f'language.{language}')

        reply_markup = self.keyboard_factory.language_menu(user_available_new_languages)
        await self.message_service.handle_interaction(update, self.language_manager.t('language.choose'), reply_markup=reply_markup)

    async def update_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):        
        _, new_language = self.message_service.get_callback_data(update)
        user_id = self.message_service.get_user_id(update)

        self.language_manager.set_language(new_language)
        await self.message_service.edit_inline_message(update, self.language_manager.t('main.menu.loading'))

        self.user_data_manager.update_user_language(user_id, new_language)
        
        await self.show_languages(update, context)