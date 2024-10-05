# app/services/chat.py

from sqlalchemy.orm import Session
from app.dao.chat import ChatDAO
from app.schemas.chat import ChatMessageCreate, ChatSessionCreate
from app.agent.agent import process_message

class ChatService:
    @staticmethod
    def create_session(db: Session):
        return ChatDAO.create_session(db)

    @staticmethod
    def send_message(db: Session, session_id: str, message: ChatMessageCreate):
        # Save user message
        user_message = ChatDAO.create_message(db, message, session_id)
        
        # Process the message with the agent and get a bot response
        bot_response_content = process_message(message.content)
        
        # Create a bot message
        bot_message = ChatMessageCreate(
            sender="bot",
            content=bot_response_content,
            message_type="bot"
        )
        
        # Save the bot message in the database (or simulate the saving process)
        bot_message_record = ChatDAO.create_message(db, bot_message)
        
        # Return the bot message (complete ChatMessage schema)
        return bot_message_record  # This now includes the id, session_id, and created_at fields

    @staticmethod
    def get_chat_history(db: Session, session_id: str):
        return ChatDAO.get_chat_history(db, session_id)
