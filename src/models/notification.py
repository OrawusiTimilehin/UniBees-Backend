from beanie import Document, Indexed
from datetime import datetime
from pydantic import Field

class Notification(Document):
    """
    Notification Model
    """
    to_user_id: Indexed(str)
    from_user_id: str
    from_name: str
    type: str = "FRIEND_REQUEST"
    message: str
    status: str = "PENDING" # PENDING, ACCEPTED, IGNORED
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "notifications"