# main.py
from fastapi import FastAPI, HTTPException
from app.config.mongo import connect_to_mongo
from app.config.weaviate import connect_to_weaviate
from app.routes import chat, user, vector, skills
from contextlib import asynccontextmanager
import logging
from app.config import config  # Import config after other initializations

# Create FastAPI application instance
app = FastAPI()

# Validate environment variables
# config.validate()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Initialize databases
        await connect_to_mongo()
        await connect_to_weaviate()
        logging.info("Application setup complete.")
        yield
    except Exception as e:
        logging.exception("Error during application setup.")
        raise HTTPException(status_code=500, detail="Application startup failed.")
    finally:
        logging.info("Application cleanup complete.")

# Use lifespan context manager
app = FastAPI(lifespan=lifespan)

# Include routers with prefixes and tags
app.include_router(user.router, prefix="/v1/user", tags=["User"])
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat"])
app.include_router(vector.router,prefix="/v1/vector",tags=["Vector"])
app.include_router(skills.router,prefix="/v1/skills",tags=["Skills"])

# Example endpoint
@app.get("/")
async def root():
    return {"message": "Resume bot Application is running!"}