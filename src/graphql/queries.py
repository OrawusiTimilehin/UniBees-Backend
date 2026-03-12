import strawberry
from typing import Optional, List
from src.models.user import User
from src.graphql.types import UserType, SwarmType
from src.models.swarm import Swarm



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
    



@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info: strawberry.Info) -> Optional[UserType]:
        """Retrieves the currently logged-in bee."""
        user_id = info.context.get("user_id")
        if not user_id:
            return None
        return await User.get(user_id)

    @strawberry.field
    async def swarms(self) -> List[SwarmType]:
        """
        THE MISSING QUERY:
        Fetches all active swarms from the hive, sorted by nectar quality.
        """
        # Fetch all swarms from MongoDB
        all_swarms = await Swarm.find_all().to_list()
        
        # Sort by nectar quality descending (Highest first) in memory
        return sorted(all_swarms, key=lambda s: s.nectar_quality, reverse=True)

    @strawberry.field
    async def get_user(self, id: str) -> Optional[UserType]:
        """Fetches a specific bee by their ID."""
        return await User.get(id)
    


    # --- In queries.py ---
    @strawberry.field
    async def my_swarms(self, info: strawberry.Info) -> List[SwarmType]:
        """Fetches all swarms created by the currently logged-in bee."""
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Not authenticated")
        
        swarms = await Swarm.find(Swarm.creator_id == user_id).to_list()
        return swarms
