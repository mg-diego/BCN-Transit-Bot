from collections import defaultdict
import json
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from providers.helpers import logger

class MessageService:
    """
    Service responsible for sending, editing, and caching Telegram messages
    for users, including handling callback queries and web app data.
    """

    def __init__(self, bot=None):
        """
        Initialize the MessageService.

        :param bot: Optional Telegram bot instance.
        """
        self._bot = bot
        self._user_messages = defaultdict(list)
        logger.info(f"[{self.__class__.__name__}] MessageService initialized")

    def set_bot_instance(self, bot):
        """Inject the bot instance (optional for testing or external use)."""
        self._bot = bot
        logger.info(f"[{self.__class__.__name__}] Bot instance set")

    async def handle_interaction(self, update: Update, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=ParseMode.HTML):
        """
        Send or edit a message depending on the type of interaction:
        - callback_query (inline button)
        - message (text)
        - web_app_data (update.message.web_app_data)
        """
        if update.callback_query:
            logger.info(f"[{self.__class__.__name__}] Handling callback_query for user {self.get_user_id(update)}")
            return await self.edit_inline_message(update, text, reply_markup, parse_mode)
        elif update.message:
            logger.info(f"[{self.__class__.__name__}] Handling message for user {self.get_user_id(update)}")
            return await self.send_new_message(update, text, reply_markup, parse_mode)

    async def send_new_message(self, update: Update, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=ParseMode.HTML):
        """Send a new message (does not edit)."""
        msg = await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        self._cache_message(update, msg)
        logger.info(f"[{self.__class__.__name__}] Sent new message {msg.message_id} to user {self.get_user_id(update)}")
        return msg
    
    async def send_new_message_from_bot(self, bot, user_id, text, parse_mode=ParseMode.HTML):
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=parse_mode
        )

    async def edit_inline_message(self, update: Update, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=ParseMode.HTML):
        """Edit a message originating from an inline button (callback_query)."""
        query = update.callback_query
        await query.answer()
        msg = await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        self._cache_message(update, msg)
        logger.info(f"[{self.__class__.__name__}] Edited inline message {msg.message_id} for user {self.get_user_id(update)}")
        return msg

    async def send_message_direct(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=ParseMode.HTML):
        """Send a message directly to a chat by ID (e.g., from web_app_data)."""
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        self._user_messages[chat_id].append(msg.message_id)
        logger.info(f"[{self.__class__.__name__}] Sent direct message {msg.message_id} to chat {chat_id}")
        return msg

    async def edit_message_by_id(self, chat_id: int, message_id: int, text: str, reply_markup: InlineKeyboardMarkup = None, parse_mode=ParseMode.HTML):
        """Edit a previously sent message using chat_id and message_id."""
        if not self._bot:
            raise ValueError("Bot instance not set. Use set_bot_instance() first.")
        await self._bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        logger.info(f"[{self.__class__.__name__}] Edited message {message_id} in chat {chat_id}")

    async def send_new_message_from_callback(self, update: Update, text: str, reply_markup=None, parse_mode=ParseMode.HTML):
        """
        Send a new message in the context of an inline button (callback_query).
        """
        if not self._bot:
            raise ValueError("Bot instance not set. Use set_bot_instance(bot) first.")
        msg = await self._bot.send_message(
            chat_id=self.get_chat_id(update),
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        self._cache_message(update, msg)
        logger.info(f"[{self.__class__.__name__}] Sent new callback message {msg.message_id} to user {self.get_user_id(update)}")
        return msg

    async def send_location(self, update: Update, latitude: str, longitude: str, reply_markup=None):
        """
        Send a location message to the user.
        """
        if not self._bot:
            raise ValueError("Bot instance not set. Use set_bot_instance(bot) first.")
        msg = await self._bot.send_location(
            chat_id=self.get_chat_id(update),
            latitude=latitude,
            longitude=longitude,
            reply_markup=reply_markup
        )
        self._cache_message(update, msg)
        logger.info(f"[{self.__class__.__name__}] Sent location to user {self.get_user_id(update)}: ({latitude}, {longitude})")
        return msg
    
    async def send_map_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE, line_name):
        await context.bot.send_photo(
            chat_id=self.get_chat_id(update),
            photo=f"https://www.tmb.cat/documents/20182/242926/{line_name}+TERMOMETRE+HORZ.jpg",
        )

    def _cache_message(self, update, msg):
        """Store the message_id in the user's cache."""
        user_id = self.get_user_id(update)
        self._user_messages[user_id].append(msg.message_id)
        logger.debug(f"[{self.__class__.__name__}] Cached message {msg.message_id} for user {user_id}")

    async def clear_user_messages(self, user_id: int):
        """
        Delete all messages sent to a user and clear the cache.
        """
        if not self._bot:
            raise ValueError("Bot instance not set. Use set_bot_instance(bot) first.")

        chat_id = user_id  # usually user_id == chat_id in private bots
        if user_id in self._user_messages:
            for msg_id in self._user_messages[user_id]:
                try:
                    await self._bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    logger.info(f"[{self.__class__.__name__}] Deleted message {msg_id} for user {user_id}")
                except Exception as e:
                    logger.warning(f"[{self.__class__.__name__}] Error deleting message {msg_id}: {e}")
            self._user_messages[user_id].clear()

    # Utility methods
    def extract_context(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Return common info: user_id, chat_id, line_id, stop_id (if available)"""
        self.set_bot_instance(context.bot)
        user_id = self.get_user_id(update)
        chat_id = self.get_chat_id(update)
        line_id = None
        stop_id = None

        if update.message and update.message.web_app_data:
            data = json.loads(update.message.web_app_data.data)
            stop_id = data.get("stop_id").strip()
            line_id = data.get("line_id").strip()
        elif update.callback_query:
            callback_data = self.get_callback_data(update)
            line_id = callback_data[1] if len(callback_data) > 1 else None
            stop_id = callback_data[2] if len(callback_data) > 2 else None

        return user_id, chat_id, line_id, stop_id
    
    def get_callback_query(self, update):
        return update.callback_query.data if update.callback_query else None
    
    def check_query_callback(self, update, expected_callback):
        """Check if callback_query data starts with the expected callback string."""
        return update.callback_query.data.startswith(expected_callback)

    def get_callback_data(self, update):
        """Split callback_query data by ':' and return list."""
        return update.callback_query.data.split(":")

    def get_user_id(self, update):
        """Return user ID from update."""
        return update.callback_query.from_user.id if update.callback_query else update.message.from_user.id

    def get_username(self, update):
        """Return user's first name from update."""
        return update.callback_query.from_user.first_name if update.callback_query else update.message.from_user.first_name

    def get_chat_id(self, update):
        """Return chat ID from update."""
        return update.callback_query.message.chat_id if update.callback_query else update.message.chat_id
