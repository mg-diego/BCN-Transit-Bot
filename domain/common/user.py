from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class User:
    user_id: int
    username: str
    initial_start: datetime
    last_start: datetime
    uses: int
    language: str
    receive_notifications: bool
    already_notified: List[int] = field(default_factory=list)
