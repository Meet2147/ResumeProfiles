import weaviate
from weaviate.auth import AuthApiKey
from weaviate.classes.init import Auth
from app.config.config import Config  # Import centralized configuration
import logging
from fastapi import HTTPException
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


# Initialize Weaviate client
client: weaviate.Client = None
executor = ThreadPoolExecutor(max_workers=1)  # Executor to run synchronous queries asynchronously

async def connect_to_weaviate():
    try:
        # Attempt to connect to Weaviate
#         client = weaviate.connect_to_weaviate_cloud(
#             cluster_url=Config.WEAVIATE_REST_URL,
#             auth_credentials=Auth.api_key(Config.WEAVIATE_API_KEY),
# )
        # Connect to Weaviate Cloud Python_V3
        client = weaviate.Client(
            url=Config.WEAVIATE_REST_URL,
            auth_client_secret=weaviate.auth.AuthApiKey(api_key=Config.WEAVIATE_API_KEY),
)
        # Check if the connection is successful by calling the .is_ready() method
        if not client.is_ready():
            raise Exception("Weaviate is not ready.")
        
        # Log success message
        logger.info("Successfully connected to Weaviate.")
        
        return client
    except Exception as e:
        logger.error(f"Error connecting to Weaviate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to Weaviate: {str(e)}")
        
async def connect_to_weaviate1():
    """Initialize and connect the Weaviate client."""
    global client
    try:
        # client = weaviate.Client(
        #     url=Config.WEAVIATE_REST_URL,
        #     auth_client_secret=AuthApiKey(api_key=Config.WEAVIATE_API_KEY),
        #     timeout_config=(5, 15)  # Custom timeout settings
        # )
        # client = weaviate.use_async_with_weaviate_cloud(
        #    cluster_url=Config.WEAVIATE_REST_URL,  # Replace with your Weaviate Cloud URL
        #    auth_credentials=Auth.api_key(api_key=Config.WEAVIATE_API_KEY),  # Replace with your Weaviate Cloud key
        #    headers={'X-OpenAI-Api-key': Config.openai_api_key} 
        #    )
        if client.is_ready():
            print("Weaviate connected successfully!")
        else:
            raise ConnectionError("Weaviate is not ready.")
    except Exception as e:
        print(f"Error connecting to Weaviate: {e}")
        raise

def get_weaviate_client():
    if client is None:
        raise Exception("Weaviate client is not initialized. Please call connect_to_weaviate() first.")
    return client

# Synchronous function to fetch user data
def fetch_user_data_sync(user_id: str):
    """Fetch user data synchronously."""
    try:
        # Construct the query
        query = client.query.get("Resume", ["name", "email"]).with_where({
            "path": ["user_id"], 
            "operator": "Equal", 
            "valueInt": user_id  # Use valueInt for integer fields
        })

        # Execute the query using do() instead of get()
        result = query.do()

        # Debugging: Print the raw result to understand its structure
        print("Query result:", result)

        # Check if the result contains any data
        if result and result.get('data', {}).get('Get', {}).get('Resume'):
            return result['data']['Get']['Resume'][0]
        else:
            print(f"No data found for user_id {user_id}")
            return None
    except Exception as e:
        print(f"Error fetching data for user_id {user_id}: {e}")
        return None


# Asynchronous function to fetch user data using an executor
async def fetch_user_data_async(user_id: str):
    """Fetch user data asynchronously using an executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, fetch_user_data_sync, user_id)