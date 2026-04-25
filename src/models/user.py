from beanie import Document, Indexed
from datetime import datetime
from typing import List, Optional
from pydantic import EmailStr, Field
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

class User(Document):
    """
    User Model
    Defines the identity  of each bee in the hive.
    """
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    password: str
    name: str
    major: str = "Undecided"
    rank: str = "LARVA" 
    interests: List[str] = []
    swarms_joined: List[str] = []
    image: str = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=400"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    friends: List[str] = []
    swarms_joined: List[str] = []
    image: str = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=400"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    participated_swarms: List[str] = []
    swipes_today: int = 0
    last_swipe_reset: datetime= Field(default_factory=datetime.utcnow)
    seen_bee_ids: List[str] = []
    liked_bee_ids: List[str] = [] 

    class Settings:
        name = "users" 

    def check_and_reset_quota(self):
        now = datetime.datetime.utcnow()
        if self.last_swipe_reset.date() < now.date():
            self.swipes_today = 0
            self.last_swipe_reset = now

    async def set_password(self, plain_password: str):
        """
        Hashes the password before storing.
        With Argon2, there is no longer a 72-character limit.
        """
        self.password = pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        """
        Verifies a plain text password against the stored hash.
        Handles both new Argon2 hashes and old Bcrypt hashes automatically.
        """
        return pwd_context.verify(plain_password, self.password)
    
    class Settings:
        name = "users"

    async def set_password(self, plain_password: str):
        self.password = pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        return pwd_context.verify(plain_password, self.password)

    @classmethod
    async def by_email(cls, email: str) -> Optional["User"]:
        """Helper to find a user by email."""
        return await cls.find_one(cls.email == email.lower())
    
    