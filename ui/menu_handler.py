from telegram import Update
from telegram.ext import (
    ContextTypes
)

class MenuHandler:
    def __init__(self, keyboard_factory, message_service, user_data_manager):
        self.keyboard_factory = keyboard_factory
        self.message_service = message_service
        self.user_data_manager = user_data_manager

    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.user_data_manager.register_user(self.message_service.get_user_id(update), self.message_service.get_username(update))
        await self.message_service.handle_interaction(update, "¡Bienvenido al bot! Elige una opción:", reply_markup=self.keyboard_factory.create_main_menu())
