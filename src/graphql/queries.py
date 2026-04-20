import strawberry
from typing import Optional, List
from src.models.user import User
from src.models.swarm import Swarm
from src.models.message import Message
from src.models.notification import Notification
from src.graphql.types import UserType, SwarmType, MessageType, NotificationType

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