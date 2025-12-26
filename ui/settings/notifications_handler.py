from telegram import Update
from telegram.ext import ContextTypes

from domain.clients import ClientType
from ui.keyboard_factory import KeyboardFactory
from application import MessageService
from providers.manager import LanguageManager, UserDataManager, audit_action

class NotificationsHandler:

    def __init__(self, message_service: MessageService, keyboard_factory: KeyboardFactory, language_manager: LanguageManager, user_data_manager: UserDataManager):
        self.message_service = message_service
        self.keyboard_factory = keyboard_factory
        self.language_manager = language_manager
        self.user_data_manager = user_data_manager

    async def show_current_configuration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.message_service.get_user_id(update)
        enabled_notifications = await self.user_data_manager.get_user_receive_notifications(ClientType.TELEGRAM.value, user_id)
        msg_key = 'settings.notifications.enabled' if enabled_notifications else 'settings.notifications.disabled'
        await self.message_service.handle_interaction(
            update,
            self.language_manager.t(msg_key),
            reply_markup=self.keyboard_factory.update_notifications(enabled_notifications)
        )

    async def update_user_configuration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = self.message_service.get_user_id(update)
        _, new_value = self.message_service.get_callback_data(update)
        await self.user_data_manager.update_user_receive_notifications(ClientType.TELEGRAM.value, user_id, new_value)
        await self.show_current_configuration(update, context)
