from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection
from app.config.config import Config  # Import centralized configuration

# Initialize MongoDB client
client: AsyncIOMotorClient = None
db = None

async def connect_to_mongo():
    """Establish a connection to MongoDB."""
    global client, db
    try:
        # Construct the MongoDB URI
        mongo_uri = f"mongodb://{Config.MONGO_HOST}:{Config.MONGO_PORT}/{Config.MONGO_DB_NAME}"
        client = AsyncIOMotorClient(mongo_uri)
        db = client[Config.MONGO_DB_NAME]
        print("MongoDB connected successfully!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close the MongoDB connection."""
    if client:
        client.close()
        print("MongoDB connection closed.")

def get_user_collection() -> Collection:
    """Return the user collection."""
    if not db:
        raise ValueError("Database connection is not initialized. Call 'connect_to_mongo()' first.")
    return db[Config.USER_COLLECTION_NAME]

# def get_resume_collection() -> Collection:
#     """Return the resume collection."""
#     if not db:
#         raise ValueError("Database connection is not initialized. Call 'connect_to_mongo()' first.")
#     return db[Config.RESUME_COLLECTION_NAME]

def get_user_collection() -> Collection:
    """Returns the user collection from the MongoDB database."""
    return db[Config.USER_COLLECTION_NAME]

def get_resume_collection() -> Collection:
    return db[Config.RESUME_COLLECTION_NAME]