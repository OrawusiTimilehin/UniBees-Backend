import datetime
import strawberry
from typing import List, Optional

@strawberry.type
class UserType:
    id: str
    username: str
    email: str
    name: str
    major: str
    rank: str
    interests: List[str]
    image: str

@strawberry.type
class SwarmType:
    id: str
    name: str
    description: str
    tags: List[str] 
    creator_id: str
    members: List[str]
    # Making this optional to prevent frontend crashes if a record is missing the field
    nectar_quality: Optional[float] 
    image: str


@strawberry.type
class MessageType:
    id: str
    swarm_id: str
    sender_id: str
    sender_name: str
    sender_image: str
    text: str
    timestamp: datetime.datetime

@strawberry.type
class AuthPayload:
    token: str
    user: UserType