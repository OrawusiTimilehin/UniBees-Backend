from beanie import Document, Indexed
from datetime import datetime
from typing import List, Optional
from pydantic import EmailStr, Field
from passlib.context import CryptContext

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Document):
    """
    User Model
    Defines the identity and "Pollen" (interests) of each bee in the hive.
    Uses Beanie ODM for MongoDB.
    """
    username: Indexed(str, unique=True)
    email: Indexed(EmailStr, unique=True)
    password: str
    name: str
    major: str = "Undecided"
    rank: str = "LARVA"  # Enum equivalent: ['LARVA', 'WORKER BEE', 'SCOUT', 'ELDER BEE']
    interests: List[str] = []
    image: str = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=400"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"  # Collection name in MongoDB

    async def set_password(self, plain_password: str):
        """Hashes the password before storing."""
        self.password = pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        """Verifies a plain text password against the stored hash."""
        return pwd_context.verify(plain_password, self.password)

    @classmethod
    async def by_email(cls, email: str) -> Optional["User"]:
        """Helper to find a user by email."""
        return await cls.find_one(cls.email == email.lower())