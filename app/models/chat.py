from pydantic import BaseModel
from typing import List

class ChatMessage(BaseModel):
    user_id: str
    message: str
    timestamp: str

class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage]
