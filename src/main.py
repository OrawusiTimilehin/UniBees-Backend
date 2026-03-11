import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
from strawberry.fastapi import GraphQLRouter

# Import models, schema, and the AUTH helper
from app.models.user import User
from app.graphql.schema import schema
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

# --- THE AUTH INTEGRATION ---
async def get_context(request: Request):
    """
    This function runs before every GraphQL operation.
    It uses our middleware to check for a user_id in the headers.
    """
    user_id = get_user_id_from_request(request)
    return {"user_id": user_id}

# Pass the context_getter to the router
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

@app.on_event("startup")
async def startup_event():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    await init_beanie(database=client.unibees_db, document_models=[User])
    print("🚀 Hive Database Connected with Auth Middleware")

@app.get("/")
async def root():
    return {"message": "UniBees Hive API is active."}