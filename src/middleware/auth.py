import jwt
import os
from typing import Optional
from fastapi import Request
from dotenv import load_dotenv

# CRITICAL: Load env here to ensure JWT_SECRET is available immediately
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")

def get_user_id_from_request(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    
    try:
        # HS256 will automatically check the 'exp' (30 days) claim
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        # This tells the context the session is specifically EXPIRED
        return "EXPIRED"
    except (jwt.InvalidTokenError, Exception):
        return None