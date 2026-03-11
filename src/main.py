import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv
from strawberry.fastapi import GraphQLRouter

# Import your models and the schema
from src.models.user import User
from src.graphql.schema import schema
from src.middleware.auth import get_user_id_from_request

load_dotenv()

app = FastAPI(title="UniBees Hive API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#  * THE AUTH HANDSHAKE
#  * This function runs before every single GraphQL request.
#  * It uses your auth helper to see if a valid token exists.
 

async def get_context(request: Request):
    user_id = get_user_id_from_request(request)
    # This dictionary becomes the 'info.context' in your resolvers
    return {"user_id": user_id}

# Initialize the GraphQL Router with the context_getter
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

@app.on_event("startup")
async def startup_event():
    # Initialize MongoDB via Beanie
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    await init_beanie(database=client.unibees_db, document_models=[User])
    print("🚀 Hive DB Connected & Auth Context Active")

@app.get("/")
async def root():
    return {"message": "UniBees Hive API is active."}