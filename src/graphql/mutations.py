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
        2. Hashes password securely.
        3. Saves to MongoDB Atlas.
        """
        # Ensure email is lowercase for consistency
        email_clean = email.lower()
        
        existing = await User.find_one(User.email == email_clean)
        if existing:
            raise Exception("This email is already registered in the hive!")

        # Create the Beanie document
        new_user = User(
            username=username,
            email=email_clean,
            password="", # Placeholder, set below
            name=name
        )
        
        # Hash the password using our model helper
        await new_user.set_password(password)
        
        # Insert into Atlas
        await new_user.insert()

        # Generate session token
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