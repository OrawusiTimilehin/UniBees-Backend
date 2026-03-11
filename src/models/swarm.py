from beanie import Document, Indexed
from datetime import datetime
from typing import List, Optional
from pydantic import Field

class Swarm(Document):
    """
    Swarm Model
    Represents a student group or interest-based community.
    """
    name: Indexed(str, unique=True)
    description: str
    pollen_type: str  # The primary interest/category of the group
    creator_id: str
    members: List[str] = []
    nectar_quality: float = 0.0 # Reputation/Activity score
    image: str = "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=400"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "swarms"