from telegram import Update
from telegram.ext import (
    CallbackContext,
    ContextTypes
)

class MenuHandler:
    def __init__(self, keyboard_factory, message_service, navigation_history):
        self.keyboard_factory = keyboard_factory
        self.message_service = message_service
        self.navigation_history = navigation_history

    async def commnand_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("¡Bienvenido al bot! Elige una opción:", reply_markup=self.keyboard_factory.create_main_menu())


    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.message_service.send_or_edit_message(update, context, "¡Bienvenido al bot! Elige una opción:", reply_markup=self.keyboard_factory.create_main_menu())
