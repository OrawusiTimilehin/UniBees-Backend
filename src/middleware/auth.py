import jwt
import os
from typing import Optional
from fastapi import Request

def get_user_id_from_request(request: Request) -> Optional[str]:
    """
    Extracts and decodes the JWT from the 'Authorization: Bearer <token>' header.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(
            token, 
            os.getenv("JWT_SECRET", "hive_secret_key"), 
            algorithms=["HS256"]
        )
        return payload.get("user_id")
    except:
        return None