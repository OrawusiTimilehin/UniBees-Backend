from dotenv import load_dotenv
import strawberry
import jwt
import os
from datetime import datetime, timedelta
from typing import List, Optional
from src.middleware.auth import get_user_id_from_request
from src.models.user import User
from src.graphql.types import UserType, AuthPayload
from src.models.swarm import Swarm
from src.graphql.types import UserType, AuthPayload, SwarmType
from src.models.notification import Notification
from src.graphql.types import NotificationType  


# Load environment variables from .env file
load_dotenv()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is not set. The hive cannot start securely.")

def create_token(user_id: str) -> str:
    """
    Generates a secure Digital ID (JWT) with expiration.
    - exp: Token expires in 30 days.
    - iat: Identifies the time at which the JWT was issued.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@strawberry.type
class Mutation:
    # --- SIGNUP & LOGIN (Existing) ---
    @strawberry.mutation
    async def signup(self, username: str, email: str, password: str, name: str) -> AuthPayload:
        email_clean = email.lower()
        existing = await User.find_one(User.email == email_clean)
        if existing:
            raise Exception("Bee already exists in the hive!")
        new_user = User(username=username, email=email_clean, password="", name=name)
        await new_user.set_password(password)
        await new_user.insert()
        return AuthPayload(token=create_token(str(new_user.id)), user=new_user)

    @strawberry.mutation
    async def login(self, email: str, password: str) -> AuthPayload:
        user = await User.find_one(User.email == email.lower())
        if not user or not user.verify_password(password):
            raise Exception("Invalid credentials")
        return AuthPayload(token=create_token(str(user.id)), user=user)

    # --- PROFILE UPDATES (NEW) ---

    @strawberry.mutation
    async def update_interests(self, info: strawberry.Info, interests: List[str]) -> UserType:
        """Updates the user's pollen (interests) list."""
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("You must be logged in to update your interests.")
        
        user = await User.get(user_id)
        if not user:
            raise Exception("User not found.")
            
        user.interests = interests
        await user.save() # Saves changes to MongoDB Atlas
        return user

    @strawberry.mutation
    async def change_password(self, info: strawberry.Info, new_password: str) -> str:
        """Securely updates the bee's password."""
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Unauthorized action.")
        
        user = await User.get(user_id)
        # Hashing happens inside the set_password model helper
        await user.set_password(new_password)
        await user.save()
        
        return "Password successfully updated."

    @strawberry.mutation
    async def update_major(self, info: strawberry.Info, major: str) -> UserType:
        """Updates the bee's field of study in the hive."""
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Unauthorized.")
        
        user = await User.get(user_id)
        if not user:
            raise Exception("User not found.")

        user.major = major
        await user.save()
        return user
    
    @strawberry.mutation
    async def update_image(self, info: strawberry.Info, image: str) -> UserType:
        """Saves the Base64 image string to the user's document in MongoDB."""
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Unauthorized.")
        
        user = await User.get(user_id)
        if not user:
            raise Exception("User not found.")

        user.image = image
        await user.save()
        return user
    

 # --- SWARM OPERATIONS ---

    @strawberry.mutation
    async def create_swarm(
        self, 
        info: strawberry.Info, 
        name: str, 
        description: str,
        tags: List[str],
        nectar_quality: float = 0.0,
    ) -> SwarmType:
        """Establishes a new Swarm (Group) in the hive."""
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Login required to create a swarm.")
        
        new_swarm = Swarm(
            name=name,
            description=description,
            creator_id=user_id,
            members=[user_id]
        )
        await new_swarm.insert()
        return new_swarm

    @strawberry.mutation
    async def join_swarm(self, info: strawberry.Info, swarm_id: str) -> SwarmType:
        """Adds the logged-in bee to an existing swarm."""
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Unauthorized.")

        swarm = await Swarm.get(swarm_id)
        if not swarm:
            raise Exception("Swarm not found.")

        if user_id not in swarm.members:
            swarm.members.append(user_id)
            await swarm.save()
            
        return swarm
    


    @strawberry.mutation
    async def update_swarm(
        self, 
        info: strawberry.Info, 
        swarm_id: str, 
        description: Optional[str] = None, 
        tags: Optional[List[str]] = None,
        image: Optional[str] = None
    ) -> SwarmType:
        """Allows the creator to update swarm details."""
        user_id = info.context.get("user_id")
        swarm = await Swarm.get(swarm_id)
        
        if not swarm:
            raise Exception("Swarm not found")
        if swarm.creator_id != user_id:
            raise Exception("Only the queen of this swarm can edit its details!")

        if description is not None:
            swarm.description = description
        if tags is not None:
            swarm.tags = tags
        if image is not None:
            swarm.image = image
            
        await swarm.save()
        return swarm
    

    @strawberry.mutation
    async def join_swarm(self, info: strawberry.Info, swarm_id: str) -> SwarmType:
        """Adds the bee to the swarm and updates the user's joined list."""
        user_id = info.context.get("user_id")
        if not user_id:
            raise Exception("Unauthorized. Please log in.")

        swarm = await Swarm.get(swarm_id)
        user = await User.get(user_id)
        
        if not swarm or not user:
            raise Exception("Swarm or User not found.")

        # 1. Update Swarm Members
        if user_id not in swarm.members:
            swarm.members.append(user_id)
            await swarm.save()
            
        # 2. Update User's Joined Swarms
        if swarm_id not in user.swarms_joined:
            user.swarms_joined.append(swarm_id)
            await user.save()
            
        return swarm
    
    @strawberry.mutation
    async def respond_to_friend_request(
        self, 
        info: strawberry.Info, 
        notification_id: str, 
        action: str
    ) -> bool:
        # 1. FIX: Access context as a dictionary if dot notation fails
        try:
            request = info.context.request
        except AttributeError:
            request = info.context["request"]

        my_id = get_user_id_from_request(request)
        if not my_id: return False

        # 2. GHOST ID CHECK (Prevents the PydanticObjectId crash)
        if notification_id.startswith("temp-"):
            return True

        # 3. PROCEED WITH DB LOGIC
        notif = await Notification.get(notification_id)
        if not notif: return False

        if action == "ACCEPT":
            me = await User.get(my_id)
            sender = await User.get(notif.from_user_id)

            if me and sender:
                # Ensure friends list exists and update
                if not hasattr(me, 'friends') or me.friends is None: me.friends = []
                if not hasattr(sender, 'friends') or sender.friends is None: sender.friends = []

                if str(sender.id) not in me.friends:
                    me.friends.append(str(sender.id))
                    await me.save()
                
                if str(me.id) not in sender.friends:
                    sender.friends.append(str(me.id))
                    await sender.save()
                
                print(f"✅ {me.name} and {sender.name} are now friends!")

        await notif.delete()
        return True

    @strawberry.mutation
    async def delete_notification(self, info: strawberry.Info, notification_id: str) -> bool:
        notif = await Notification.get(notification_id)
        if notif:
            await notif.delete()
        return True
    
