from beanie import Document, Indexed
import datetime
from typing import Optional
from pydantic import Field

class Notification(Document):
    """
    Notification Model
    Stores friend requests and hive alerts so they persist
    even if the user is offline.
    """
    to_user_id: Indexed(str)
    from_user_id: str
    from_name: str
    type: str = "FRIEND_REQUEST" # e.g., FRIEND_REQUEST, SYSTEM_ALERT
    message: str
    status: str = "PENDING" # PENDING, ACCEPTED, IGNORED

    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Settings:
        name = "notifications"