import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
import socketio
from strawberry.fastapi import GraphQLRouter

# Import models & schema
from src.models.user import User
from src.models.swarm import Swarm
from src.models.message import Message
# Note: Ensure you create a Notification model in your models folder
from src.models.notification import Notification 

from src.graphql.schema import schema
from src.middleware.auth import get_user_id_from_request

load_dotenv()

app = FastAPI(title="UniBees Hive API")

# --- THE FIX: Robust CORS Configuration ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GraphQL Setup ---
async def get_context(request: Request):
    user_id = get_user_id_from_request(request)
    return {"user_id": user_id}

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

# --- Socket.io Setup ---
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

@app.on_event("startup")
async def startup_event():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    # Ensure all social models are initialized here
    await init_beanie(
        database=client.unibees_db, 
        document_models=[User, Swarm, Message, Notification]
    )
    print("🚀 Hive DB Connected & Social Features Active")

# --- Socket.io Event Handlers ---

@sio.event
async def connect(sid, environ):
    print(f"Bee connected: {sid}")

@sio.event
async def join_swarm(sid, data):
    """Adds a bee to a specific swarm room for group chat."""
    swarm_id = data.get("swarm_id")
    if swarm_id:
        await sio.enter_room(sid, swarm_id)
        print(f"Bee {sid} joined swarm {swarm_id}")

@sio.event
async def identify_bee(sid, data):
    """
    Users join a private room named after their user_id.
    This allows the server to send them direct notifications (friend requests).
    """
    user_id = data.get("user_id")
    if user_id:
        await sio.enter_room(sid, user_id)
        print(f"Bee {user_id} is now reachable for private notifications")

@sio.event
async def send_message(sid, data):
    """Group messaging persistence and broadcast."""
    swarm_id = data.get("swarm_id")
    new_msg = Message(
        swarm_id=swarm_id,
        sender_id=data.get("sender_id") or data.get("senderId"),
        sender_name=data.get("sender_name") or data.get("senderName"),
        sender_image=data.get("sender_image") or data.get("senderImage") or "",
        text=data.get("text"),
        timestamp=datetime.utcnow()
    )
    await new_msg.insert()
    broadcast_data = new_msg.to_dict() if hasattr(new_msg, 'to_dict') else data
    await sio.emit("receive_message", broadcast_data, room=swarm_id)

@sio.event
async def send_friend_request(sid, data):
    """
    Handles real-time friend request alerts.
    'to_user_id' is the ID of the person whose name was clicked.
    """
    target_user_id = data.get("to_user_id")
    sender_name = data.get("from_name")
    
    notification = {
        "type": "FRIEND_REQUEST",
        "message": f"{sender_name} wants to join your swarm!",
        "from_user_id": data.get("from_user_id"),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Send only to the specific user's room
    await sio.emit("new_notification", notification, room=target_user_id)
    print(f"Notification sent to {target_user_id} from {sender_name}")

@sio.event
async def send_friend_request(sid, data):
    to_id = data.get("to_user_id")
    from_name = data.get("from_name", "Unknown Bee") # Ensure this exists!
    
    new_notif = Notification(
        to_user_id=to_id,
        from_user_id=data.get("from_user_id"),
        from_name=from_name,
        message=f"{from_name} wants to connect!"
    )
    
    await new_notif.insert()
    
    await sio.emit("new_notification", {
        "id": str(new_notif.id), # MongoDB ID
        "from_name": from_name,
        "from_user_id": data.get("from_user_id"),
        "message": new_notif.message
    }, room=to_id)


@sio.event
async def send_private_message(sid, data):
    recipient_id = data.get("recipient_id")
    sender_id = data.get("sender_id")
    
    # Persist in MongoDB
    new_msg = Message(
        recipient_id=recipient_id,
        sender_id=sender_id,
        sender_name=data.get("sender_name"),
        text=data.get("text"),
        timestamp=datetime.utcnow()
    )
    await new_msg.insert()

    # Emit to the recipient's room
    await sio.emit("receive_private_message", new_msg.to_dict(), room=recipient_id)
    
    # Emit back to sender (to sync messages across multiple open tabs)
    await sio.emit("receive_private_message", new_msg.to_dict(), room=sender_id)




@sio.event
async def disconnect(sid):
    print(f"Bee left the hive: {sid}")