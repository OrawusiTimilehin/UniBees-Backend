import strawberry
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional

# Using 'src' prefix to match your directory structure
from src.models.user import User
from src.graphql.types import UserType, AuthPayload

def create_token(user_id: str):
    """
    Generates a JWT (Digital ID Card) for the bee.
    Stored in the frontend to keep the user logged in.
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET", "hive_secret_key"), algorithm="HS256")

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def signup(
        self, 
        username: str, 
        email: str, 
        password: str, 
        name: str
    ) -> AuthPayload:
        """
        Registers a new Bee in the hive.
        1. Checks for existing email.
        2. Hashes password securely via the User model.
        3. Saves to MongoDB Atlas using Beanie's insert().
        """
        # Ensure email is lowercase for consistency
        email_clean = email.lower()
        
        # 1. Search Atlas for an existing bee
        existing = await User.find_one(User.email == email_clean)
        if existing:
            raise Exception("This email is already registered in the hive!")

        # 2. Create the Beanie document instance
        new_user = User(
            username=username,
            email=email_clean,
            password="", # Placeholder, will be hashed below
            name=name
        )
        
        # 3. Hash the password using the helper defined in the Canvas
        await new_user.set_password(password)
        
        # 4. STORE IN MONGODB: This is the line that performs the save
        await new_user.insert()

        # 5. Generate session token
        token = create_token(str(new_user.id))
        
        return AuthPayload(
            token=token,
            user=UserType(
                id=str(new_user.id),
                username=new_user.username,
                email=new_user.email,
                name=new_user.name,
                major=new_user.major,
                rank=new_user.rank,
                interests=new_user.interests,
                image=new_user.image
            )
        )

    @strawberry.mutation
    async def login(self, email: str, password: str) -> AuthPayload:
        """
        Verifies a bee's credentials and issues a new token.
        """
        user = await User.find_one(User.email == email.lower())
        
        if not user or not user.verify_password(password):
            raise Exception("The credentials provided do not match our hive records.")

        token = create_token(str(user.id))
        
        return AuthPayload(
            token=token,
            user=UserType(
                id=str(user.id),
                username=user.username,
                email=user.email,
                name=user.name,
                major=user.major,
                rank=user.rank,
                interests=user.interests,
                image=user.image
            )
        )

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