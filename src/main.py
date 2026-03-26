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
    allow_origins=origins, # Specifically allow your frontend
    allow_credentials=True,
    allow_methods=["*"],    # Allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],    # Allow Authorization, Content-Type, etc.
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
    await init_beanie(
        database=client.unibees_db, 
        document_models=[User, Swarm, Message]
    )
    print("🚀 Hive DB Connected & CORS Policy Active")

# --- THE FIX: Socket.io Event Handlers for Database Persistence ---

@sio.event
async def connect(sid, environ):
    print(f"Bee connected: {sid}")

@sio.event
async def join_swarm(sid, data):
    """Adds a bee to a specific swarm room for targeted broadcasting."""
    swarm_id = data.get("swarm_id")
    if swarm_id:
        await sio.enter_room(sid, swarm_id)
        print(f"Bee {sid} joined swarm {swarm_id}")

@sio.event
async def send_message(sid, data):
    """
    Receives a message from the frontend, persists it to MongoDB,
    and broadcasts it back to everyone in the swarm.
    """
    swarm_id = data.get("swarm_id")
    
    # 1. Map incoming data to our Beanie Message model
    # Note: Using data.get to safely handle both snake_case and camelCase from frontend
    new_msg = Message(
        swarm_id=swarm_id,
        sender_id=data.get("sender_id") or data.get("senderId"),
        sender_name=data.get("sender_name") or data.get("senderName"),
        sender_image=data.get("sender_image") or data.get("senderImage") or "",
        text=data.get("text"),
        timestamp=datetime.utcnow()
    )

    # 2. Persist to MongoDB Atlas
    await new_msg.insert()

    # 3. Broadcast to everyone in the swarm room (Real-time)
    # We include the new DB generated ID in the broadcast
    broadcast_data = new_msg.to_dict() if hasattr(new_msg, 'to_dict') else data
    await sio.emit("receive_message", broadcast_data, room=swarm_id)
    print(f"Buzz saved and broadcasted in swarm {swarm_id}")

@sio.event
async def disconnect(sid):
    print(f"Bee left the hive: {sid}")
    