import strawberry
from typing import Optional, List
from src.models.user import User
from src.graphql.types import UserType, SwarmType, MessageType
from src.models.swarm import Swarm
from src.models.message import Message



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
    
      # --- In queries.py ---
    @strawberry.field
    async def my_swarms(self, info: strawberry.Info) -> List[SwarmType]:
        """Fetches all swarms created by the currently logged-in bee."""
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Not authenticated")
        
        swarms = await Swarm.find(Swarm.creator_id == user_id).to_list()
        return swarms

    
    @strawberry.field
    async def get_swarm(self, id: str) -> Optional[SwarmType]:
        """Fetches a swarm, ensuring the ID is valid for MongoDB."""
        try:
            # Try fetching by direct ID string (Beanie handles conversion)
            swarm = await Swarm.get(id)
            return swarm
        except Exception:
            return None

    @strawberry.field
    async def get_swarm_messages(self, swarm_id: str) -> List[MessageType]:
        """Chronological messages for the chat UI."""
        messages = await Message.find(
            Message.swarm_id == swarm_id
        ).sort("-timestamp").limit(50).to_list()
        return messages[::-1]
    
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


  
