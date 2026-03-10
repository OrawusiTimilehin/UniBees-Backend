import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
from strawberry.fastapi import GraphQLRouter

# Import our models and the unified schema
from app.models.user import User
from app.graphql.schema import schema

# Load .env from the root directory
load_dotenv()

app = FastAPI(title="UniBees Hive API")

# CORS configuration for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """
    Initializes the connection to MongoDB Atlas and 
    sets up Beanie with our User model.
    """
    db_uri = os.getenv("MONGODB_URI")
    if not db_uri:
        raise ValueError("MONGODB_URI is missing from your .env file!")
    
    client = AsyncIOMotorClient(db_uri)
    
    # Initialize Beanie with the User blueprint
    await init_beanie(
        database=client.unibees_db, 
        document_models=[User]
    )
    print("🚀 Hive Database Connected (Auth Only Mode)")

# This is your GraphQL entry point
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root():
    return {"message": "UniBees Hive API is active."}