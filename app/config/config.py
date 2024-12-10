from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

class Config:
    """Application configuration loaded from environment variables."""

    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
    MONGO_HOST = os.getenv("MONGO_HOST")
    MONGO_PORT = os.getenv("MONGO_PORT")
    MONGO_USER = os.getenv("MONGO_USER")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
    WEAVIATE_REST_URL = os.getenv("WEAVIATE_REST_ENDPOINT")
    WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
    openai_api_key = os.getenv("openai_api_key")
    RESUME_COLLECTION_NAME=os.getenv("RESUME_COLLECTION_NAME")

    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set."""
        required_vars = [
            "MONGO_DB_NAME",
            "MONGO_HOST",
            "MONGO_PORT",
            "WEAVIATE_REST_URL",
            "WEAVIATE_API_KEY",
            "openai_api_key",
            "RESUME_COLLECTION_NAME"
        ]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        if missing_vars:
            error_message = f"Missing required environment variables: {', '.join(missing_vars)}"
            raise EnvironmentError(error_message)
        print("All required environment variables are set.")
