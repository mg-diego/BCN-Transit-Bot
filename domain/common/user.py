from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass
class User:
    user_id: str
    username: str
    created_at: datetime
    language: str
    receive_notifications: bool
    already_notified: List[int] = field(default_factory=list)
    fcm_token: str = ""
