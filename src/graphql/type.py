import strawberry
from typing import List, Optional

@strawberry.type
class UserType:
    """
    The public-facing 'Type Definition' for a Bee.
    We exclude sensitive fields like 'password' here.
    """
    id: str
    username: str
    email: str
    name: str
    major: str
    rank: str
    interests: List[str]
    image: str

@strawberry.type
class AuthPayload:
    """
    The shape of the response after a successful Login or Signup.
    """
    token: str
    user: UserType