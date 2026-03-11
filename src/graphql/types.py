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
    pollen_type: str
    creator_id: str
    members: List[str]
    nectar_quality: float
    image: str

@strawberry.type
class AuthPayload:
    token: str
    user: UserType