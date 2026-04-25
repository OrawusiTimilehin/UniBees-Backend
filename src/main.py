import os
import json
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
# Ensure this matches your Vite frontend port (usually 5173)
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
# Set logger=True to see every single packet in your terminal for debugging
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*', logger=False, engineio_logger=False)
socket_app = socketio.ASGIApp(sio, app)

@app.on_event("startup")
async def startup_event():
    try:
        client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        await init_beanie(
            database=client.unibees_db, 
            document_models=[User, Swarm, Message, Notification]
        )
        print("🚀 Hive persistence layers active (Messages, Swarms, Notifications & Matching)")
    except Exception as e:
        print(f"❌ DATABASE STARTUP ERROR: {e}")

# --- Socket.io Event Handlers ---

@sio.event
async def connect(sid, environ):
    print(f"📡 Bee connected to socket: {sid}")

@sio.event
async def identify_bee(sid, data):
    """
    CRITICAL SESSION FIX:
    Maps the connection to a room named exactly after the user_id.
    """
    if not data: return
    
    # Handle both {user_id: "..."} and direct string input
    raw_id = data.get("user_id") if isinstance(data, dict) else data
    user_id = str(raw_id).strip()

    if user_id and user_id != "None" and user_id != "undefined":
        # Leave any old rooms first to prevent ghosting
        rooms = sio.rooms(sid)
        for room in rooms:
            if room != sid: await sio.leave_room(sid, room)
            
        await sio.enter_room(sid, user_id)
        await sio.save_session(sid, {"user_id": user_id})
        print(f"🆔 Bee {user_id} identified and locked into private room.")
    else:
        print(f"⚠️ Identification failed: Received invalid ID '{user_id}'")

@sio.event
async def join_swarm(sid, data):
    if not data: return
    swarm_id = str(data.get("swarm_id") if isinstance(data, dict) else data).strip()
    
    if swarm_id:
        await sio.enter_room(sid, swarm_id)
        session = await sio.get_session(sid) or {}
        session["current_swarm"] = swarm_id
        await sio.save_session(sid, session)

        # Real-time Presence Tracking
        participants = sio.manager.rooms.get('/', {}).get(swarm_id, set())
        active_count = len(participants)

        await sio.emit("swarm_presence_update", {
            "swarm_id": swarm_id,
            "active_bees": active_count
        }, room=swarm_id)
        print(f"🏠 Bee {sid} joined group swarm: {swarm_id} (Total: {active_count})")

@sio.event
async def send_message(sid, data):
    """Unified Swarm Messaging Handler with Stigmergic Algorithm."""
    swarm_id = str(data.get("swarm_id")).strip()
    text = data.get("text")
    sender_id = str(data.get("sender_id") or data.get("senderId")).strip()
    sender_name = data.get("sender_name") or data.get("senderName")

    try:
        new_msg = Message(
            swarm_id=swarm_id,
            sender_id=sender_id,
            sender_name=sender_name,
            text=text,
            timestamp=datetime.utcnow()
        )
        await new_msg.insert()

        # Update User Participation for Matching Algorithm
        user = await User.get(sender_id)
        if user and swarm_id not in user.participated_swarms:
            user.participated_swarms.append(swarm_id)
            await user.save()

        # Run Pheromone Algorithm
        swarm = await Swarm.get(swarm_id)
        if swarm:
            curr_p = getattr(swarm, 'pheromone_base', 10.0) or 10.0
            recent_count = await Message.find(Message.swarm_id == swarm_id, Message.timestamp > datetime.utcnow() - timedelta(minutes=5)).count()
            r_multiplier = 1.0 + (min(recent_count, 20) / 20.0)
            actual_boost = (2.5 * r_multiplier) * (1 - (curr_p / 100.0))
            await swarm.update({"$set": {
                "pheromone_base": min(100.0, curr_p + actual_boost),
                "last_buzz_at": datetime.utcnow()
            }})

        # BROADCAST: Ensure the model has to_dict or fallback to raw dict
        payload = new_msg.to_dict() if hasattr(new_msg, 'to_dict') else json.loads(new_msg.json())
        await sio.emit("receive_message", payload, room=swarm_id)
        print(f"💬 Swarm buzz from {sender_name} synced in {swarm_id}")

    except Exception as e:
        print(f"❌ SWARM MESSAGE ERROR: {e}")

@sio.event
async def send_private_message(sid, data):
    """Direct Bee-to-Bee communication via room routing."""
    recipient_id = str(data.get("recipient_id") or data.get("recipientId")).strip()
    sender_id = str(data.get("sender_id") or data.get("senderId")).strip()
    sender_name = data.get("sender_name") or data.get("senderName")
    text = data.get("text")
    
    print(f"📩 Routing buzz: {sender_id} -> {recipient_id}")

    try:
        new_msg = Message(
            recipient_id=recipient_id, 
            sender_id=sender_id, 
            sender_name=sender_name, 
            text=text, 
            timestamp=datetime.utcnow()
        )
        await new_msg.insert()
        
        payload = new_msg.to_dict() if hasattr(new_msg, 'to_dict') else json.loads(new_msg.json())
        
        # 1. Send to Recipient's Room
        await sio.emit("receive_private_message", payload, room=recipient_id)
        # 2. Send back to Sender (for sync across multiple tabs/devices)
        await sio.emit("receive_private_message", payload, room=sender_id)
        
        print(f"✅ Real-time private buzz delivered to rooms.")
    except Exception as e:
        print(f"❌ PRIVATE MESSAGE ERROR: {e}")

@sio.event
async def handle_swipe(sid, data):
    """Enforces 5-swipe limit and checks for Hive Matches."""
    user_id = str(data.get("user_id")).strip()
    target_id = str(data.get("target_id")).strip()
    action = data.get("action")

    try:
        me = await User.get(user_id)
        target = await User.get(target_id)
        if not me or not target: return

        # Quota Logic
        now = datetime.utcnow()
        if me.last_swipe_reset.date() < now.date():
            me.swipes_today = 0
            me.last_swipe_reset = now
        
        if me.swipes_today >= 5:
            await sio.emit("swipe_error", {"message": "Hive Quota Reached (5/5)"}, room=user_id)
            return

        me.swipes_today += 1
        me.seen_bee_ids.append(target_id)
        
        if action == "LIKE":
            me.liked_bee_ids.append(target_id)
            if user_id in target.liked_bee_ids:
                if target_id not in me.friends: me.friends.append(target_id)
                if user_id not in target.friends: target.friends.append(user_id)
                
                match_notif = {"type": "MATCH", "partner_name": target.name, "partner_id": target_id}
                await sio.emit("new_match", match_notif, room=user_id)
                await sio.emit("new_match", {**match_notif, "partner_name": me.name, "partner_id": user_id}, room=target_id)
        
        await me.save()
        await target.save()
        await sio.emit("swipe_success", {"swipes_today": me.swipes_today}, room=user_id)
    except Exception as e:
        print(f"❌ SWIPE ERROR: {e}")

@sio.event
async def disconnect(sid):
    session = await sio.get_session(sid)
    if session and "current_swarm" in session:
        swarm_id = session["current_swarm"]
        participants = sio.manager.rooms.get('/', {}).get(swarm_id, set())
        active_count = len(participants)
        await sio.emit("swarm_presence_update", {"swarm_id": swarm_id, "active_bees": active_count}, room=swarm_id)
    print(f"👋 Bee disconnected: {sid}")

# RUN COMMAND: uvicorn main:socket_app --reload --port 8000