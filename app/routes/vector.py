from fastapi import APIRouter
from pydantic import BaseModel  # Import BaseModel for Pydantic model
from controllers.vector_controller import handle_uploaded_resume
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
from fastapi import File, UploadFile


router = APIRouter()

# class Message(BaseModel):  # Define a model for the request body
#     message: str

class QueryRequest(BaseModel):
    query: str

@router.get("/")
async def chat_root():
    print("hit from vector router")
    return {"message": "Welcome to the vector API"}

@router.post("/send")
async def upload_resume(file: UploadFile = File(...)):
    print("hit from vector router post api")
    result = await handle_uploaded_resume(file)
    return result

# @router.post("/send")
# async def process_assets(msg: Message):  # Use the Pydantic model here
#     print("hit from vector router post api")
#     generate_vectors(msg.message)
#     return {"message": "Message sent", "content": msg.message}