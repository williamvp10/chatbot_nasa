# app/dao/chat.py

from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatSessionCreate, ChatMessageCreate
import uuid
from datetime import datetime

class ChatDAO:
    @staticmethod
    def get_session_by_user_and_channel(db: Session, user_id: str, channel: str):
        """
        Busca una sesión activa por usuario y canal de comunicación.
        """
        return db.query(ChatSession).filter(ChatSession.user_id == user_id, ChatSession.channel == channel).first()

    @staticmethod
    def create_session(db: Session, user_id: str, channel: str) -> ChatSession:
        """
        Crea una nueva sesión de chat para un usuario en un canal específico.
        """
        session_id = str(uuid.uuid4())  # Generar un UUID único para la sesión
        new_session = ChatSession(session_id=session_id, user_id=user_id, channel=channel)
        db.add(new_session)
        db.commit()
        return new_session

    @staticmethod
    def get_session_by_id(db: Session, session_id: str):
        return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()

    @staticmethod
    def create_message(db: Session, message: ChatMessageCreate, session_id: str):
        """
        Crea un nuevo mensaje de chat y lo asocia a una sesión mediante session_id.
        """
        db_message = ChatMessage(
            sender=message.sender,
            content=message.content,
            message_type=message.message_type,
            session_id=session_id,  # Usar el session_id correcto
            created_at=datetime.utcnow()
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message  # Return the full ChatMessage, which includes the ID, session_id, and created_at

    @staticmethod
    def get_chat_history(db: Session, session: ChatSession, limit: int = 10):
        return db.query(ChatMessage).filter(ChatMessage.session_id == session.session_id).order_by(ChatMessage.created_at.desc()).limit(limit).all()