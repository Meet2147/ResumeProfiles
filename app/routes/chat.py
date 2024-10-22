from fastapi import APIRouter
from controllers.chat_controller import process_user_message

router = APIRouter()

@router.get("/")
async def chat_root():
    print("hit from chat router")
    return {"message": "Welcome to the chat API"}

@router.post("/send_message")
async def send_message(message: str):
    print("hit from chat router", message)
    result = await process_user_message(message)
    return {"message": "Message sent", "content": result}

