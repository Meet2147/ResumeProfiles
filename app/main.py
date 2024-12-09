from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from contextlib import asynccontextmanager  

# Import database connection functions
from app.config.mongo import connect_to_mongo
from app.config.weaviate import connect_to_weaviate, get_weaviate_client
from app.routes import chat, user, vector,skills

from fastapi import FastAPI, HTTPException, Depends
from dotenv import load_dotenv
from contextlib import asynccontextmanager  


# Load environment variables
load_dotenv()

# Create FastAPI application instance
app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application setup and cleanup."""
    try:
        # Connect to MongoDB and Weaviate
        await connect_to_mongo()
        await connect_to_weaviate()
        print("Application setup complete")
        yield
    except Exception as e:
        print(f"Error during application setup: {e}")
        raise HTTPException(status_code=500, detail="Application startup failed.")
    finally:
        # Perform any necessary cleanup if needed
        print("Application cleanup complete.")

# Use lifespan context manager
app = FastAPI(lifespan=lifespan)

# Include routers with prefixes and tags
app.include_router(user.router, prefix="/v1/user", tags=["User"])
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat"])
app.include_router(vector.router,prefix="/v1/vector",tags=["Vector"])
app.include_router(skills.router,prefix="/v1/skills",tags=["Skills"])
# app.include_router(user.router, prefix="/v1/user", tags=["User"])

# Dependency to ensure the Weaviate client is available
async def weaviate_client_dependency():
    return get_weaviate_client()

@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Welcome to the RAG Pipeline Chatbot API"}

