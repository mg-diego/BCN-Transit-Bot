import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from providers.helpers import logger
from application import UpdateManager  # Reutilizamos tu clase existente


class LoadingMessageManager:
    """
    Manages animated loading messages (⏳., ⏳.., ⏳...) per user.
    Uses UpdateManager to handle async animation tasks.
    """

    def __init__(self):
        self.update_manager = UpdateManager()
        self.messages: dict[int, int] = {}  # user_id -> message_id
        logger.info(f"[{self.__class__.__name__}] Initialized")

    
