import weaviate
from weaviate.auth import AuthApiKey
from weaviate.classes.init import Auth
from app.config.config import Config  # Import centralized configuration
import logging
from fastapi import FastAPI, HTTPException
logger = logging.getLogger(__name__)
# Initialize Weaviate client
client: weaviate.Client = None

async def connect_to_weaviate():
    try:
        # Attempt to connect to Weaviate
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=Config.WEAVIATE_REST_URL,
            auth_credentials=Auth.api_key(Config.WEAVIATE_API_KEY),
)
        # Connect to Weaviate Cloud Python_V3
#         client = weaviate.Client(
#             url=Config.WEAVIATE_REST_URL,
#             auth_client_secret=weaviate.auth.AuthApiKey(api_key=Config.WEAVIATE_API_KEY),
# )
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
        client = weaviate.use_async_with_weaviate_cloud(
           cluster_url=Config.WEAVIATE_REST_URL,  # Replace with your Weaviate Cloud URL
           auth_credentials=Auth.api_key(api_key=Config.WEAVIATE_API_KEY),  # Replace with your Weaviate Cloud key
           headers={'X-OpenAI-Api-key': Config.openai_api_key} 
           )
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