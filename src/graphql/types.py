import strawberry
from typing import List, Optional
from datetime import datetime

@strawberry.type
class UserType:

    id: str
    username: str
    email: str
    name: str
    major: str
    rank: str
    interests: List[str]
    friends: List[str]
    swarms_joined: List[str]
    image: str

@strawberry.type
class NotificationType:

    id: str
    to_user_id: str
    from_user_id: str
    from_name: str
    type: str # e.g., "FRIEND_REQUEST"
    message: str
    status: str # "PENDING", "ACCEPTED", "IGNORED"
    created_at: datetime

@strawberry.type
class SwarmType:
  
    id: str
    name: str
    description: str
    tags: List[str]
    creator_id: str
    members: List[str]
    nectar_quality: float
    image: str

@strawberry.type
class MessageType:
 
    id: str
    swarm_id: Optional[str]
    recipient_id: Optional[str]
    sender_id: str
    sender_name: str
    text: str
    timestamp: datetime

@strawberry.type
class AuthPayload:

    token: str
    user: UserType