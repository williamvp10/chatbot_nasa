# app/api/chat.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.chat import ChatMessageCreate, ChatMessage, ChatSession
from app.services.chat import ChatService

router = APIRouter()

@router.post("/session/", response_model=ChatSession)
def create_chat_session(db: Session = Depends(get_db)):
    session = ChatService.create_session(db)
    return session

@router.post("/message/", response_model=ChatMessage)
def send_chat_message(
    message: ChatMessageCreate,
    session_id: str,
    db: Session = Depends(get_db)
):
    try:
        bot_message = ChatService.send_message(db, session_id, message)
        return bot_message
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/history/", response_model=list[ChatMessage])
def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    try:
        return ChatService.get_chat_history(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
