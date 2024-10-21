import os
from dotenv import load_dotenv
import weaviate
import logging
from fastapi import FastAPI, HTTPException
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

client = None

async def connect_to_weaviate():
    try:
        # Attempt to connect to Weaviate
        client = weaviate.Client("http://localhost:8080")  # Assuming Weaviate is running locally
        
        # Check if the connection is successful by calling the .is_ready() method
        if not client.is_ready():
            raise Exception("Weaviate is not ready.")
        
        # Log success message
        logger.info("Successfully connected to Weaviate.")
        
        return client
    except Exception as e:
        logger.error(f"Error connecting to Weaviate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to Weaviate: {str(e)}")
    
# async def connect_to_weaviate():
#     global client
    
#     # Read from environment variables
#     http_host = os.getenv("WEAVIATE_HTTP_HOST", "localhost")  # Default to localhost if not set
#     http_port = int(os.getenv("WEAVIATE_HTTP_PORT", 8080))  # Default to 8080 if not set
#     grpc_host = os.getenv("WEAVIATE_GRPC_HOST", "localhost")  # Default to localhost if not set
#     grpc_port = int(os.getenv("WEAVIATE_GRPC_PORT", 9090))  # Default to 9090 if not set
    
#     connection_params = ConnectionParams(
#         http={"scheme": "http", "host": http_host, "port": http_port, "secure": False},
#         grpc={"scheme": "http", "host": grpc_host, "port": grpc_port, "secure": False}
#     )
    
#     client = WeaviateClient(connection_params=connection_params)
#     print("Connected to Weaviate")

def get_weaviate_client():
    if client is None:
        raise Exception("Weaviate client is not initialized. Please call connect_to_weaviate() first.")
    return client
