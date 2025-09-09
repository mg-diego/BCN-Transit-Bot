from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class AuditLogger:
    def __init__(self, worksheet, max_buffer_size=50):
        """
        :param worksheet: Hoja de Google Sheets donde se escriben los audit logs.
        :param max_buffer_size: Tamaño máximo del buffer antes de hacer flush automático.
        """
        self.worksheet = worksheet
        self.buffer = []
        self.max_buffer_size = max_buffer_size

    def add_event(self, user_id, username, chat_type, action_type, command_or_button, callback=None, params=None, bot_version="1.5-beta"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        event = {
            "timestamp": now,
            "user_id": user_id,
            "username": username,
            "chat_type": chat_type,
            "action_type": action_type,
            "command_or_button": command_or_button,
            "callback": callback or "",
            "params": json.dumps(params, ensure_ascii=False) if params else "",
            "bot_version": bot_version
        }
        self.buffer.append(event)

        # Si llegamos al límite, hacemos flush automático
        if len(self.buffer) >= self.max_buffer_size:
            self.flush()

    def flush(self):
        if not self.buffer:
            return

        try:
            rows = [[
                e["timestamp"],
                e["user_id"],
                e["username"],
                e["chat_type"],
                e["action_type"],
                e["command_or_button"],
                e["callback"],
                e["params"],
                e["bot_version"]
            ] for e in self.buffer]

            self.worksheet.append_rows(rows)
            logger.debug(f"Flushed {len(rows)} audit events to Google Sheets.")
        except Exception as e:
            logger.error(f"Failed to flush audit events: {e}")
        finally:
            self.buffer.clear()
