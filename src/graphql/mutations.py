import strawberry
import jwt
import os
from datetime import datetime, timedelta
from typing import List, Optional
from src.models.user import User
from src.graphql.types import UserType, AuthPayload

def create_token(user_id: str):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET", "hive_secret_key"), algorithm="HS256")

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
    
@strawberry.type
class Mutation:
    # ... existing mutations (signup, login, update_interests, change_password) ...

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