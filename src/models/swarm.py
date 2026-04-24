from beanie import Document, Indexed
from datetime import datetime
from typing import List
from pydantic import Field

class Swarm(Document):
    """
    Swarm Model
    Replaced single pollen_type with a list of tags for better categorization.
    """
    name: Indexed(str, unique=True)
    description: str
    tags: List[str] = [] 
    creator_id: str
    members: List[str] = []
    nectar_quality: float = 0.0 # Activity/Reputation score
    image: str = "https://images.unsplash.com/photo-1517048676732-d65bc937f952?w=400"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    pheromone_base: float = Field(default=10.0)
    upvotes: int = Field(default=0)
    last_buzz_at: datetime = Field(default_factory=datetime.utcnow)


    class Settings:
        name = "swarms"

    