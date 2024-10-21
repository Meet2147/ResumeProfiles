from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def chat_root():
    print("hit from chat router")
    return {"message": "Welcome to the chat API"}

@router.post("/send")
async def send_message(message: str):
    # Your message handling logic here
    print("hit from chat router")
    return {"message": "Message sent", "content": message}
