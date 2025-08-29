from telegram import Update
from telegram.ext import ContextTypes

from ui.keyboard_factory import KeyboardFactory

class SettingsHandler:

    def __init__(self, message_service, keyboard_factory: KeyboardFactory, language_manager):
        self.message_service = message_service
        self.keyboard_factory = keyboard_factory
        self.language_manager = language_manager

    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.message_service.handle_interaction(update, self.language_manager.t('settings.message'), reply_markup=self.keyboard_factory.settings_replykeyboard())
