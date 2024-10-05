# app/api/whatsapp.py

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session
from app.services.whatsapp import WhatsAppService
from app.db.session import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/webhook/")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    Verification endpoint for WhatsApp webhook.
    """
    if hub_verify_token == settings.VERIFY_TOKEN:
        return int(hub_challenge)  # Return the challenge provided by Facebook to verify
    else:
        raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post("/webhook/")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Handle incoming WhatsApp webhook message.
    """
    try:
        data = await request.json()
        response = await WhatsAppService.handle_incoming_message(db, data, background_tasks)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
