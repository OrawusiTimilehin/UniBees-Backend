import os
from datetime import datetime, timedelta
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
from src.models.notification import Notification 

from src.graphql.schema import schema
from src.middleware.auth import get_user_id_from_request

load_dotenv()

app = FastAPI(title="UniBees Hive API")

# --- CORS Configuration ---
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
    try:
        client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        await init_beanie(
            database=client.unibees_db, 
            document_models=[User, Swarm, Message, Notification]
        )
        print("🚀 Hive persistence layers active (Messages, Swarms, & Notifications)")
    except Exception as e:
        print(f"❌ DATABASE STARTUP ERROR: {e}")

# --- Socket.io Event Handlers ---

@sio.event
async def connect(sid, environ):
    print(f"Bee connected: {sid}")

@sio.event
async def identify_bee(sid, data):
    """Users join a private room named after their user_id for direct notifications."""
    user_id = data.get("user_id")
    if user_id:
        await sio.enter_room(sid, user_id)
        # We save the user_id in the socket session to track them on disconnect
        await sio.save_session(sid, {"user_id": user_id})
        print(f"📡 Bee {user_id} identified.")

@sio.event
async def join_swarm(sid, data):
    """
    Adds a bee to a specific swarm room and calculates live occupancy.
    """
    swarm_id = data.get("swarm_id")
    if swarm_id:
        await sio.enter_room(sid, swarm_id)
        
        # Link this session to the swarm for presence tracking
        session = await sio.get_session(sid) or {}
        session["current_swarm"] = swarm_id
        await sio.save_session(sid, session)

        # Calculate REAL-TIME Active Count from Socket.io Manager
        participants = sio.manager.rooms.get('/', {}).get(swarm_id, set())
        active_count = len(participants)

        # Broadcast the live count to everyone in the hive
        await sio.emit("swarm_presence_update", {
            "swarm_id": swarm_id,
            "active_bees": active_count
        }, room=swarm_id)
        
        print(f"🏠 Bee joined swarm {swarm_id}. Active connections: {active_count}")

@sio.event
async def send_message(sid, data):
    """
    Unified Swarm Messaging Handler with Smoothed Algorithm:
    1. Persists to MongoDB
    2. Runs Stigmergic Reinforcement (Smoothed)
    3. Broadcasts real-time
    """
    swarm_id = data.get("swarm_id")
    text = data.get("text")
    sender_id = data.get("sender_id") or data.get("senderId")
    sender_name = data.get("sender_name") or data.get("senderName")

    try:
        # 1. PERSISTENCE
        new_msg = Message(
            swarm_id=swarm_id,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_image=data.get("sender_image") or data.get("senderImage") or "",
            text=text,
            timestamp=datetime.utcnow()
        )
        await new_msg.insert()

        # 2. SMOOTHED STIGMERGIC REINFORCEMENT
        swarm = await Swarm.get(swarm_id)
        if swarm:
            limit = 100.0
            # Reduced base_boost (2.5) to prevent instant spikes
            base_boost = 2.5 
            current_p = getattr(swarm, 'pheromone_base', 10.0) or 10.0
            
            # Check density in the last 5 minutes (wider window = smoother growth)
            recent_count = await Message.find(
                Message.swarm_id == swarm_id,
                Message.timestamp > datetime.utcnow() - timedelta(minutes=5)
            ).count()
            
            # Scaled multiplier: requires 20 messages for full 2.0x boost
            reinforcement_r = 1.0 + (min(recent_count, 20) / 20.0)
            
            # Asymptotic Braking: The closer to 100, the harder it is to increase
            braking_factor = 1 - (current_p / limit)
            actual_boost = (base_boost * reinforcement_r) * braking_factor
            
            new_score = min(limit, current_p + actual_boost)
            
            await swarm.update({"$set": {
                "pheromone_base": new_score,
                "last_buzz_at": datetime.utcnow()
            }})

        # 3. BROADCAST
        await sio.emit("receive_message", new_msg.to_dict(), room=swarm_id)
        print(f"✅ Swarm buzz saved in {swarm_id}. New Pheromone Level: {new_score:.2f}")

    except Exception as e:
        print(f"❌ SWARM MESSAGE ERROR: {e}")

@sio.event
async def send_private_message(sid, data):
    """Handles 1-on-1 Personal Messages with persistence."""
    recipient_id = data.get("recipient_id")
    sender_id = data.get("sender_id")
    
    try:
        new_msg = Message(
            recipient_id=recipient_id,
            sender_id=sender_id,
            sender_name=data.get("sender_name"),
            text=data.get("text"),
            timestamp=datetime.utcnow()
        )
        await new_msg.insert()

        payload = new_msg.to_dict()
        await sio.emit("receive_private_message", payload, room=recipient_id)
        await sio.emit("receive_private_message", payload, room=sender_id)
        print(f"✅ Private buzz from {sender_id} to {recipient_id}")
    except Exception as e:
        print(f"❌ PRIVATE MESSAGE ERROR: {e}")

@sio.event
async def send_friend_request(sid, data):
    """Handles friend request persistence and real-time notification."""
    to_id = data.get("to_user_id")
    from_id = data.get("from_user_id")
    from_name = data.get("from_name", "A Scout Bee")
    
    try:
        new_notif = Notification(
            to_user_id=to_id,
            from_user_id=from_id,
            from_name=from_name,
            message=f"{from_name} wants to connect!",
            type="FRIEND_REQUEST",
            status="PENDING"
        )
        await new_notif.insert()
        
        await sio.emit("new_notification", {
            "id": str(new_notif.id),
            "from_name": from_name,
            "from_user_id": from_id,
            "message": new_notif.message,
            "type": "FRIEND_REQUEST",
            "timestamp": datetime.utcnow().isoformat()
        }, room=to_id)
        print(f"🔔 Notification buzzed to {to_id} from {from_name}")
    except Exception as e:
        print(f"❌ NOTIFICATION ERROR: {e}")

@sio.event
async def disconnect(sid):
    """
    Handles bee departure and updates live room counts.
    """
    session = await sio.get_session(sid)
    if session and "current_swarm" in session:
        swarm_id = session["current_swarm"]
        # Recalculate remaining bees in the room
        participants = sio.manager.rooms.get('/', {}).get(swarm_id, set())
        active_count = len(participants)
        
        await sio.emit("swarm_presence_update", {
            "swarm_id": swarm_id,
            "active_bees": active_count
        }, room=swarm_id)
        
    print(f"Bee left the hive: {sid}")

