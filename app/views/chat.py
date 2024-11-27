from fastapi import APIRouter, HTTPException
from app.controllers.chat_controller import process_user_message
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/")
async def chat(request: ChatRequest):
    print("hit in views for chat")
    response = await process_user_message(request)
    return ChatResponse(response=response)
