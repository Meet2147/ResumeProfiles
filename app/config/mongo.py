from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection
import os
from urllib.parse import quote_plus

# Load environment variables
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "default_db_name")
USER_COLLECTION_NAME = os.getenv("USER_COLLECTION_NAME", "users")  # Default collection name
RESUME_COLLECTION_NAME = os.getenv("RESUME_COLLECTION_NAME", "employees")  # Default collection name

# Set username and password (update these with your actual credentials if needed)
# username = quote_plus("user@name")  # Change as necessary
# password = quote_plus("my@password")  # Change as necessary
host = "localhost"
port = "27017"
db_name = MONGO_DB_NAME

# Create the MongoDB URI
# MONGO_URI = f"mongodb://{username}:{password}@{host}:{port}/{db_name}"
MONGO_URI = f"mongodb://{host}:{port}/{db_name}"
print(f"Using MONGO_URI: {MONGO_URI}")

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client[db_name]

async def connect_to_mongo():
    global client
    client = AsyncIOMotorClient(MONGO_URI)
    print("Connected to MongoDB")

def get_mongo_client():
    return client

def get_user_collection() -> Collection:
    """Returns the user collection from the MongoDB database."""
    return db[USER_COLLECTION_NAME]

def get_resume_collection() -> Collection:
    return db[RESUME_COLLECTION_NAME]
