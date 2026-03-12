import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
from strawberry.fastapi import GraphQLRouter

# Import models
from src.models.user import User
from src.models.swarm import Swarm # Ensure this is imported
from src.graphql.schema import schema
from src.middleware.auth import get_user_id_from_request

load_dotenv()

app = FastAPI(title="UniBees Hive API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_context(request: Request):
    user_id = get_user_id_from_request(request)
    return {"user_id": user_id}

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

@app.on_event("startup")
async def startup_event():
    # Initialize MongoDB via Beanie
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    
    # THE FIX: Add 'Swarm' to the document_models list.
    # This tells Beanie to monitor the 'swarms' collection.
    await init_beanie(
        database=client.unibees_db, 
        document_models=[User, Swarm] 
    )
    print("🚀 Hive DB Connected (Users & Swarms Active)")

@app.get("/")
async def root():
    return {"message": "UniBees Hive API is active."}