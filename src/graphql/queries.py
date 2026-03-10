import strawberry
from typing import Optional
from src.models.user import User
from src.graphql.types import UserType

@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info) -> Optional[UserType]:
        """
        Retrieves the profile of the bee currently logged in.
        Note: Context logic for JWT will be added in the middleware step.
        """
        # Placeholder: returning None until middleware is wired up
        return None

    @strawberry.field
    async def get_user(self, id: str) -> Optional[UserType]:
        """
        Fetches a specific Bee from the hive using their MongoDB ID.
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