import datetime
from beanie import Document, Indexed
from typing import Optional
from pydantic import Field

class Message(Document):
    """
    Message Model

    """
    # swarm_id is used for group chats (Swarms)
    swarm_id: Optional[Indexed(str)] = None
    
    # recipient_id is used for direct messages between bees
    recipient_id: Optional[Indexed(str)] = None
    
    sender_id: Indexed(str)
    sender_name: str
    
    text: str
    
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    class Settings:
        name = "messages"
        # Indexes ensure that loading the last 50 messages 
        # in a busy swarm stays lightning fast.
        indexes = [
            [("swarm_id", 1), ("timestamp", -1)],
            [("sender_id", 1), ("recipient_id", 1), ("timestamp", -1)]
        ]