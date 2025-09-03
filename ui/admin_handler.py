from datetime import datetime
import os
from pathlib import Path
import html
import subprocess
from typing import List
from telegram import Update
from telegram.ext import CallbackContext
from telegram.constants import ParseMode
from providers.helpers import logger


class AdminHandler:
    def __init__(self, bot, admin_id):
        """
        Initialize the AdminCommands handler.

        Args:
            admin_ids (list[int]): Telegram user IDs allowed to use admin commands.
        """
        self.bot = bot
        self.admin_ids = [int(admin_id)]
        self.start_time = datetime.now()
        self.MAX_LENGTH = 4000
        logger.info(f"AdminHandler initialized for admin_id={admin_id}")

    def get_current_commit(self) -> str:
        """
        Returns the latest git commit information of the bot:
        <date> - <commit_message>
        <hash>
        """
        try:
            output = subprocess.check_output(
                ["git", "log", "-1", "--pretty=format:%cd - %s%n%H", "--date=short"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            logger.debug(f"Fetched current commit: {output}")
            return output
        except Exception as e:
            logger.error(f"Error fetching commit: {e}")
            return f"Error fetching commit: {e}"
        
    def tail_log(self, file_path: str = "logs/app.log", lines: int = 50) -> List[str]:
        """
        Returns the last `lines` lines of the log file.
        """
        log_file = Path(file_path)
        if not log_file.exists():
            logger.warning(f"Log file '{file_path}' not found.")
            return [f"Log file '{file_path}' not found."]

        try:
            with log_file.open("rb") as f:
                f.seek(0, 2)
                end_pos = f.tell()
                chunk_size = 1024
                data = bytearray()
                pointer = end_pos
                while pointer > 0 and data.count(b'\n') <= lines:
                    read_size = min(chunk_size, pointer)
                    pointer -= read_size
                    f.seek(pointer)
                    data[:0] = f.read(read_size)
                all_lines = data.decode(errors='ignore').splitlines()
                logger.debug(f"Read last {lines} lines from {file_path}")
                return all_lines[-lines:]
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {e}")
            return [f"Error reading log file: {e}"]

    async def _send_commit_info(self, chat_id: int):
        """Internal helper to send the current commit info to a chat."""
        commit_info = self.get_current_commit()
        await self.bot.send_message(
            chat_id=chat_id,
            text=f"🔖 Current bot commit:\n\n`{commit_info}`",
            parse_mode="Markdown"
        )
        logger.info(f"Sent current commit info to {chat_id}")

    async def commit_command(self, update: Update, context: CallbackContext):
        """Triggered when an admin uses /commit."""
        user_id = update.effective_user.id
        if user_id not in self.admin_ids:
            logger.warning(f"Unauthorized user {user_id} tried to access /commit")
            return

        await self._send_commit_info(update.effective_chat.id)

    async def send_commit_to_admins_on_startup(self):
        """Called right after the bot starts."""
        for admin_id in self.admin_ids:
            try:
                await self._send_commit_info(admin_id)
            except Exception as e:
                logger.error(f"Failed to send commit info to {admin_id}: {e}")

    async def tail_log_command(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        if user_id not in self.admin_ids:
            logger.warning(f"Unauthorized user {user_id} tried to access /logs")
            return

        try:
            num_lines = int(context.args[0]) if context.args else 50
        except ValueError:
            logger.warning(f"Invalid argument for /logs by user {user_id}: {context.args}")
            return

        log_lines = self.tail_log("logs/app.log", num_lines)
        log_text = "\n".join(log_lines)
        log_text = html.escape(log_text)

        if len(log_text) > self.MAX_LENGTH:
            log_text = log_text[-self.MAX_LENGTH:]

        logger.info(f"Admin {user_id} fetched last {num_lines} lines from log")
        await update.message.reply_text(f"<pre>{log_text}</pre>", parse_mode="HTML")

    async def uptime_command(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        if user_id not in self.admin_ids:
            logger.warning(f"Unauthorized user {user_id} tried to access /uptime")
            return

        delta = datetime.now() - self.start_time
        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        msg = f"⏱ Bot uptime: {int(hours)}h {int(minutes)}m {int(seconds)}s"
        logger.info(f"Admin {user_id} requested uptime: {msg}")
        await update.message.reply_text(msg)

    async def deploy(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        if user_id not in self.admin_ids:
            logger.warning(f"Unauthorized user {user_id} tried to access /deploy")
            return
        
        await update.message.reply_text("🚀 Starting deployment...")

        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_path = os.path.join(project_root, "scripts", "deploy.sh")
            subprocess.Popen(
                ["bash", script_path],
                cwd=project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            logger.info(f"Deploy script launched by {user_id}")

        except Exception as e:
            await update.message.reply_text(f"❌ Failed to execute deploy script:\n<pre>{e}</pre>", parse_mode=ParseMode.HTML)
            logger.error(f"Failed to launch deploy script: {e}")

    
