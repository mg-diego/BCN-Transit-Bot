import asyncio
from typing import Callable, Awaitable
from providers.helpers import logger

class UpdateManager:
    """
    Manages per-user asynchronous update tasks. Ensures that only
    one task per user is running at a time and allows cancellation.
    """

    def __init__(self):
        # Dictionary mapping user_id to asyncio Task
        self.tasks: dict[int, asyncio.Task] = {}
        logger.info(f"[{self.__class__.__name__}] UpdateManager initialized")

    def cancel_task(self, user_id: int):
        """
        Cancel the ongoing update task for a specific user, if any.

        Args:
            user_id (int): The user's ID.
        """
        task = self.tasks.pop(user_id, None)
        if task:
            task.cancel()
            logger.info(f"[{self.__class__.__name__}] Update task cancelled for user {user_id}")
        else:
            logger.debug(f"[{self.__class__.__name__}] No active update task to cancel for user {user_id}")

    def start_task(self, user_id: int, update_coro: Callable[[], Awaitable[None]]):
        """
        Start a new update task for a specific user. Cancels any existing task first.

        Args:
            user_id (int): The user's ID.
            update_coro (Callable[[], Awaitable[None]]): The coroutine function to run.
        """
        self.cancel_task(user_id)  # Prevent duplicate tasks
        task = asyncio.create_task(update_coro())
        self.tasks[user_id] = task
        logger.info(f"[{self.__class__.__name__}] Update task started for user {user_id}")
