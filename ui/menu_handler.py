from telegram import Update
from telegram.ext import (
    CallbackContext,
    ContextTypes
)

class MenuHandler:
    def __init__(self, keyboard_factory, message_service):
        self.keyboard_factory = keyboard_factory
        self.message_service = message_service

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.message_service.handle_interaction(update, "¡Bienvenido al bot! Elige una opción:", reply_markup=self.keyboard_factory.create_main_menu())
