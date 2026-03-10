import strawberry
from typing import Optional
from src.models.user import User
from src.graphql.types import UserType

@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info: strawberry.Info) -> Optional[UserType]:
        """
        Retrieves the profile of the current bee.
        'info' is a special object provided by Strawberry/GraphQL.
        We MUST type hint it as 'strawberry.Info'.
        """
        # For now, we return None. 
        # Later, we will use 'info' to check the JWT token.
        return None

    @strawberry.field
    async def get_user(self, id: str) -> Optional[UserType]:
        """
        Fetches a specific Bee from the hive.
        """
        user = await User.get(id)
        if not user:
            return None
            
        return UserType(
            id=str(user.id),
            username=user.username,
            email=user.email,
            name=user.name,
            major=user.major,
            rank=user.rank,
            interests=user.interests,
            image=user.image
        )