import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from providers.helpers import logger


class UpdateManager:
    """
    Manages per-user asynchronous update tasks.
    Now also handles animated loading messages (⏳., ⏳.., ⏳...).
    """

    def __init__(self):
        # user_id -> asyncio.Task
        self.tasks: dict[int, asyncio.Task] = {}
        # user_id -> message_id (for loading animations)
        self.loading_messages: dict[int, int] = {}
        logger.info(f"[{self.__class__.__name__}] Initialized")

    def cancel_task(self, user_id: int):
        """
        Cancel the ongoing update task for a specific user, if any.
        """
        task = self.tasks.pop(user_id, None)
        if task:
            task.cancel()
            logger.info(f"[{self.__class__.__name__}] Update task cancelled for user {user_id}")
        else:
            logger.debug(f"[{self.__class__.__name__}] No active update task to cancel for user {user_id}")

    def start_task(self, user_id: int, update_coro):
        """
        Start a new update task for a specific user.
        Cancels any existing task first.
        """
        self.cancel_task(user_id)
        task = asyncio.create_task(update_coro())
        self.tasks[user_id] = task
        logger.info(f"[{self.__class__.__name__}] Update task started for user {user_id}")

    async def _animate_loading(self, user_id: int, context: ContextTypes.DEFAULT_TYPE,
                               chat_id: int, base_text: str):
        """
        Internal coroutine that updates the message text with an animated loading indicator.
        """
        dots = 1
        message_id = self.loading_messages[user_id]
        try:
            while True:
                await asyncio.sleep(0.5)
                dots = (dots % 3) + 1
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"⏳ {base_text}{'.' * dots}"
                )
        except asyncio.CancelledError:
            logger.info(f"[{self.__class__.__name__}] Animation cancelled for user {user_id}")
            raise

    async def start_loading(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                            base_text: str = '', reply_markup = None):
        """
        Sends an initial loading message and starts the animated update task.
        """
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        # Detener cualquier animación anterior
        await self.stop_loading(update, context)

        # Enviar mensaje inicial
        message = await context.bot.send_message(chat_id=chat_id, text=f"⏳ {base_text}", reply_markup=reply_markup)
        self.loading_messages[user_id] = message.message_id

        # Crear tarea de animación usando start_task existente
        self.start_task(
            user_id,
            lambda: self._animate_loading(user_id, context, chat_id, base_text)
        )

        return message

    async def stop_loading(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Stops the animation and deletes the loading message.
        """
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # Cancelar animación si está activa
        self.cancel_task(user_id)

        '''
        # Borrar mensaje de carga si existe
        message_id = self.loading_messages.pop(user_id, None)
        if message_id:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                logger.warning(
                    f"[{self.__class__.__name__}] Could not delete loading message for user {user_id}: {e}"
                )
        '''
