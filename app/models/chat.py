# app/models/chat.py

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Integer
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    session_id = Column(String, primary_key=True, index=True, unique=True, nullable=False)  # Clave primaria
    user_id = Column(String, index=True, nullable=False)  # ID único por canal (número para WhatsApp, ID de usuario para web)
    channel = Column(String, nullable=False)  # Canal de comunicación (ej: "whatsapp", "web")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey('chat_sessions.session_id'), nullable=False)  # Relación con ChatSession
    sender = Column(String, index=True)
    content = Column(String)
    message_type = Column(String)  # 'user' o 'bot'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")
