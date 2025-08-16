from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

class MessageService:
    def __init__(self, bot=None):
        self._bot = bot

    def set_bot_instance(self, bot):
        """Inyecta la instancia del bot (opcional para pruebas o uso externo)."""
        self._bot = bot

    async def handle_interaction(self, update: Update, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=ParseMode.HTML):
        """
        Envía o edita un mensaje dependiendo del tipo de interacción:
        - callback_query (botón inline)
        - message (texto)
        - web_app_data (update.message.web_app_data)
        """
        if update.callback_query:
            await self.edit_inline_message(update, text, reply_markup, parse_mode)
        elif update.message:
            await self.send_new_message(update, text, reply_markup, parse_mode)

    async def send_new_message(self, update: Update, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=ParseMode.HTML):
        """Envía un nuevo mensaje (no edita)."""
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    async def edit_inline_message(self, update: Update, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=ParseMode.HTML):
        """Edita el mensaje proveniente de un botón inline."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    async def send_message_direct(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=ParseMode.HTML):
        """Envía un mensaje a un chat directamente con ID (por ejemplo, desde web_app_data)."""
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    async def edit_message_by_id(self, chat_id: int, message_id: int, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=ParseMode.HTML):
        """Edita un mensaje ya enviado si tienes chat_id y message_id."""
        if not self._bot:
            raise ValueError("Bot instance not set. Use set_bot_instance() first.")
        await self._bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    def get_callback_data(self, update):
        return update.callback_query.data.split(":")
    
    def get_user_id(self, update):
        return update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    
    def get_chat_id(self, update):
        return update.callback_query.message.chat_id if update.callback_query else update.message.chat_id

    async def send_new_message_from_callback(self, update: Update, text: str, reply_markup=None, parse_mode=ParseMode.HTML):
        """
        Envía un nuevo mensaje dentro del contexto de un botón inline (callback_query).
        """
        if not self._bot:
            raise ValueError("Bot instance not set. Usa set_bot_instance(bot) primero.")
        
        return await self._bot.send_message(
            chat_id=self.get_chat_id(update),
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        
    async def send_location(self, update: Update, latitude: str, longitude: str, reply_markup=None):
        if not self._bot:
            raise ValueError("Bot instance not set. Usa set_bot_instance(bot) primero.")
        
        return await self._bot.send_location(
            chat_id=self.get_chat_id(update),
            latitude=latitude,
            longitude=longitude,
            reply_markup=reply_markup
        )

