import strawberry
from typing import Optional
from src.models.user import User
from src.graphql.types import UserType

@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info: strawberry.Info) -> Optional[UserType]:
        """
        Retrieves the currently logged-in bee.
        Used to populate the Profile.jsx page.
        """
        # 1. Grab the ID from the context (set by the auth middleware)
        user_id = info.context.get("user_id")
        
        # --- DEBUG LOGS ---
        print(f"🔍 DEBUG: Auth Context User ID: {user_id}")
        
        # 2. If no ID is found in the token, we return None (triggers redirect)
        if not user_id:
            print("❌ DEBUG: No user_id found. Returning null.")
            return None

        # 3. THE MISSING PART: Fetch the REAL user from MongoDB Atlas
        user = await User.get(user_id)
        
        if not user:
            print(f"❌ DEBUG: ID {user_id} not found in Atlas.")
            return None
            
        print(f"✅ DEBUG: Found user {user.username}. Sending to Profile page.")
        
        # Return the user object so the frontend can display it
        return user

    @strawberry.field
    async def get_user(self, id: str) -> Optional[UserType]:
        """Fetches a specific bee by their ID."""
        user = await User.get(id)
        if not user:
            return None
            
        return user