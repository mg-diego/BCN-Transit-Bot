from telegram.constants import ParseMode

class MessageService:
    async def send_or_edit_message(self, update, context, text, reply_markup=None, parse_mode=ParseMode.HTML):
        """
        Envía o edita un mensaje dependiendo de si el evento proviene de un botón inline.
        """
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        elif update.message:
            await update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )

    def send_message(self, chat_id, text, reply_markup=None, parse_mode=ParseMode.HTML):
        """Envía un nuevo mensaje a un chat específico."""
        self._bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    def edit_message(self, chat_id, message_id, text, reply_markup=None, parse_mode=ParseMode.HTML):
        """Edita un mensaje ya enviado."""
        self._bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )

    def set_bot_instance(self, bot):
        """Permite inyectar la instancia del bot (útil para test o inicialización)."""
        self._bot = bot
