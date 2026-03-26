import os
import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from datetime import datetime

# Import models & schema
from src.models.user import User
from src.models.swarm import Swarm
from src.models.message import Message  # Ensure you created this from our previous step
from src.graphql.schema import schema
from src.middleware.auth import get_user_id_from_request
from strawberry.fastapi import GraphQLRouter

# 1. Initialize Socket.io Server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)

app = FastAPI(title="UniBees Hive API")

# 2. Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Socket.io Event Handlers
@sio.event
async def connect(sid, environ):
    print(f"Bee {sid} entered the hive connection.")

@sio.on("join_swarm")
async def handle_join(sid, data):
    swarm_id = data.get("swarm_id")
    sio.enter_room(sid, swarm_id)
    print(f"Bee {sid} joined swarm room: {swarm_id}")

@sio.on("send_message")
async def handle_message(sid, data):
    # Save message to MongoDB
    new_msg = Message(
        swarm_id=data["swarm_id"],
        sender_id=data["sender_id"],
        sender_name=data["sender_name"],
        sender_image=data["sender_image"],
        text=data["text"],
        timestamp=datetime.utcnow()
    )
    await new_msg.insert()
    
    # Broadcast to everyone in that specific swarm room
    await sio.emit("receive_message", data, room=data["swarm_id"])

# 4. GraphQL Setup
async def get_context(request: Request):
    user_id = get_user_id_from_request(request)
    return {"user_id": user_id}

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

@app.on_event("startup")
async def startup_event():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    await init_beanie(
        database=client.unibees_db, 
        document_models=[User, Swarm, Message]
    )
    print("🚀 Hive DB Connected (Swarms & Messages Active)")

# Mount Socket.io to the FastAPI app
app.mount("/", socket_app)