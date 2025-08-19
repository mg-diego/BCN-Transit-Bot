from telegram import Update
from telegram.ext import ContextTypes

class HelpHandler:

    def __init__(self, message_service, keyboard_factory, language_manager):
        self.message_service = message_service
        self.keyboard_factory = keyboard_factory
        self.language_manager = language_manager

    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.message_service.handle_interaction(update, self.language_manager.t('help.text'), reply_markup=self.keyboard_factory.help_menu())
