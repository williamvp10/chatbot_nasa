# app/schemas/chat.py

from datetime import datetime
from typing import List
from pydantic import BaseModel

class ChatMessageBase(BaseModel):
    sender: str
    content: str
    message_type: str  # 'user' o 'bot'

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: int
    session_id: str  # Cambiar a 'str' para que coincida con el tipo de session_id en el modelo
    created_at: datetime

    class Config:
        from_attributes = True  # Use this instead of 'orm_mode = True'

class ChatSessionBase(BaseModel):
    pass

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    session_id: str  # Usar 'session_id' en lugar de 'id' como clave primaria
    created_at: datetime
    messages: List[ChatMessage] = []

    class Config:
        from_attributes = True  # Use this instead of 'orm_mode = True'
