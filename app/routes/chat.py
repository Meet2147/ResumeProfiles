from fastapi import APIRouter
from pydantic import BaseModel
from app.controllers.chat_controller import process_user_message

router = APIRouter()

class MessageRequest(BaseModel):
    role: str
    message: str

@router.get("/")
async def chat_root():
    print("hit from chat router")
    return {"message": "Welcome to the chat API"}

@router.post("/send_message")
async def send_message(request: MessageRequest):
    print("hit from chat router", request.role, request.message)
    result = await process_user_message(request.role, request.message)
    return {"message": "Message sent", "content": result}