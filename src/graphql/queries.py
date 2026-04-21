import strawberry
from typing import Optional, List
from src.models.user import User
from src.models.swarm import Swarm
from src.models.message import Message
from src.models.notification import Notification
from src.graphql.types import UserType, SwarmType, MessageType, NotificationType
from src.middleware.auth import get_user_id_from_request
from bson import ObjectId

from utils.swarm_intelligence import calculate_current_nectar

@strawberry.type
class Query:
    #  USER QUERIES 

    @strawberry.field
    async def me(self, info: strawberry.Info) -> Optional[UserType]:
        """
        Retrieves the currently authenticated bee's profile.
        Uses the 'user_id' provided by the JWT middleware context.
        """
        user_id = info.context.get("user_id")
        if not user_id:
            return None
        return await User.get(user_id)

    @strawberry.field
    async def get_user(self, id: str) -> Optional[UserType]:
        """Fetches a specific bee by their ID for profile viewing."""
        return await User.get(id)

    @strawberry.field
    async def get_users_by_ids(self, ids: List[str]) -> List[UserType]:
        """
        Converts a list of IDs into full profiles.
        Crucial for the Personal Chats sidebar to turn the 'friends' list into names and images.
        """
        if not ids:
            return []
        # Find all users whose ID exists in the provided list
        users = await User.find({"_id": {"$in": ids}}).to_list()
        return users

    # SOCIAL & NOTIFICATION QUERIES 

    @strawberry.field
    async def notifications(self, info: strawberry.Info) -> List[NotificationType]:
        """
        Fetches all pending swarm requests for the logged-in user.
        Used for the red badge on the notification bell.
        """
        user_id = info.context.get("user_id")
        if not user_id:
            return []
        
        # We only show PENDING requests so they don't clutter the UI
        return await Notification.find(
            Notification.to_user_id == user_id,
            Notification.status == "PENDING"
        ).sort("-created_at").to_list()

    # SWARM QUERIES 

    @strawberry.field
    async def swarms(self) -> List[SwarmType]:
        """Returns all active swarms in the hive, ordered by activity/quality."""
        return await Swarm.find_all().sort("-nectar_quality").to_list()

    @strawberry.field
    async def get_swarm(self, id: str) -> Optional[SwarmType]:
        """Gets detailed information for a specific swarm room."""
        return await Swarm.get(id)

    @strawberry.field
    async def my_swarms(self, info: strawberry.Info) -> List[SwarmType]:
        """Fetches swarms created by the current user for the management dashboard."""
        user_id = info.context.get("user_id")
        if not user_id:
            return []
        return await Swarm.find(Swarm.creator_id == user_id).to_list()

    # CHAT HISTORY QUERIES 

    @strawberry.field
    async def get_swarm_messages(self, swarm_id: str) -> List[MessageType]:
        """Loads the last 50 buzzes for a specific group swarm."""
        messages = await Message.find(
            Message.swarm_id == swarm_id
        ).sort("-timestamp").limit(50).to_list()
        
        # Reverse to show them in chronological order (oldest to newest)
        return messages[::-1]

    @strawberry.field
    async def get_private_messages(self, info: strawberry.Info, other_user_id: str) -> List[MessageType]:
        """
        Loads the history for a 1-on-1 personal chat.
        Fetches messages where (Me -> Them) OR (Them -> Me).
        """
        user_id = info.context.get("user_id")
        if not user_id:
            return []

        # Complex query for bidirectional private messages
        messages = await Message.find({
            "$or": [
                {"sender_id": user_id, "recipient_id": other_user_id},
                {"sender_id": other_user_id, "recipient_id": user_id}
            ]
        }).sort("-timestamp").limit(50).to_list()

        return messages[::-1]
    
    

    @strawberry.field
    async def my_friends(self, info: strawberry.Info) -> List[UserType]:
        # 1. Get current user
        try:
            request = info.context.request
        except AttributeError:
            request = info.context["request"]
            
        my_id = get_user_id_from_request(request)
        me = await User.get(my_id)
        
        if not me or not me.friends:
            return []

        # 2. Convert string IDs to ObjectIds and find them in the 'users' collection
        # (Using set() handles those duplicate IDs we saw in your screenshot!)
        friend_object_ids = [ObjectId(f) for f in set(me.friends)]
        
        return await User.find({"_id": {"$in": friend_object_ids}}).to_list()
    
    @strawberry.field
    async def get_private_messages(self, info: strawberry.Info, other_user_id: str) -> List[MessageType]:
        # 1. Identify me
        try:
            request = info.context.request
        except AttributeError:
            request = info.context["request"]
            
        my_id = get_user_id_from_request(request)
        if not my_id: return []

        # 2. Fetch messages where (Me -> Ryan) OR (Ryan -> Me)
        messages = await Message.find({
            "$or": [
                {"sender_id": my_id, "recipient_id": other_user_id},
                {"sender_id": other_user_id, "recipient_id": my_id}
            ]
        }).sort("timestamp").to_list()

        return messages
    
    @strawberry.field
    async def swarms(self) -> List[SwarmType]:
        all_swarms = await Swarm.find_all().to_list()
        for s in all_swarms:
            # Calculate the dynamic nectar quality right before sending to React
            s.nectar_quality = calculate_current_nectar(s)
        return sorted(all_swarms, key=lambda x: x.nectar_quality, reverse=True)


