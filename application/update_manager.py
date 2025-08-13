import asyncio
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

class UpdateManager:
    def __init__(self):
        self.tasks: dict[int, asyncio.Task] = {}

    def cancel_task(self, user_id: int):
        """Cancela la tarea de actualización de un usuario."""
        task = self.tasks.pop(user_id, None)
        if task:
            task.cancel()
            logger.info(f"Tarea de actualización cancelada para usuario {user_id}")

    def start_task(self, user_id: int, update_coro: Callable[[], Awaitable[None]]):
        """Inicia la tarea de actualización para un usuario."""
        self.cancel_task(user_id)  # Evita duplicados
        task = asyncio.create_task(update_coro())
        self.tasks[user_id] = task
        logger.info(f"Tarea de actualización iniciada para usuario {user_id}")
