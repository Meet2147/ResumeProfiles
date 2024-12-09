from fastapi import APIRouter
from pydantic import BaseModel  # Import BaseModel for Pydantic model
from app.controllers.vector_controller import handle_uploaded_resume
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, PyMuPDFLoader
from fastapi import File, UploadFile
from datetime import datetime

router = APIRouter()

# class Message(BaseModel):  # Define a model for the request body
#     message: str

# class QueryRequest(BaseModel):
#     query: str

# @router.get("/")
# async def chat_root():
#     print("hit from vector router")
#     return {"message": "Welcome to the vector API"}

# @router.post("/send")
# async def upload_resume(file: UploadFile = File(...)):
#     print("hit from vector router post api")
#     result = await handle_uploaded_resume(file)
#     return result

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from app.controllers.vector_controller import handle_uploaded_resume

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

@router.get("/")
async def chat_root():
    print("hit from vector router")
    return {"message": "Welcome to the vector API"}

@router.post("/upload_resume/{user_id}")
async def upload_resume(user_id: int, file: UploadFile = File(...)):
    print("hit from vector router post api")

    # Verify that the user_id is valid before proceeding (optional)
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Pass the user_id to the handle_uploaded_resume function
    result = await handle_uploaded_resume(user_id, file)
    return result