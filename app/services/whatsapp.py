# app/services/whatsapp.py

from fastapi import BackgroundTasks
from app.services.chat import ChatService
from app.dao.chat import ChatDAO
from sqlalchemy.orm import Session
from app.schemas.chat import ChatMessageCreate
from app.agent.agent import process_message
import httpx
from app.core.config import settings
from app.services.message_processor import process_message_from_channel

class WhatsAppService:
    @staticmethod
    async def handle_incoming_message(db: Session, data: dict, background_tasks: BackgroundTasks):
        """
        Handle incoming message from WhatsApp, save it, and process it in the background.
        """
        print(data)
        # Extraemos el número y el contenido del mensaje o la ubicación
        try:
            phone_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
        except KeyError:
            return {"status": "error", "message": "Invalid payload structure"}

        # Enviar el procesamiento del mensaje a la función común
        background_tasks.add_task(process_message_from_channel, db, phone_number, message, "whatsapp", WhatsAppService.send_message_to_whatsapp)

        # 4. Return immediate response
        return {"status": "received", "message": "Received and processing"}

    @staticmethod
    async def process_agent_response(db: Session, session_id: str, phone_number: str, message_text: str):
        """
        Process the agent response and send the reply back to WhatsApp.
        """
        # Call the agent to process the message
        bot_response = process_message(message_text)  # Get response from the agent

        # Save the bot response in the chat system
        bot_message = ChatMessageCreate(
            sender="bot",
            content=bot_response,
            message_type="bot"
        )
        ChatDAO.create_message(db, bot_message)

        # 5. Send the bot response back to the user via WhatsApp API
        await WhatsAppService.send_message_to_whatsapp(phone_number, bot_response)

    @staticmethod
    async def send_message_to_whatsapp(phone_number: str, message_text: str):
        """
        Send the message back to the user via WhatsApp API.
        """
        
        whatsapp_url = f"https://graph.facebook.com/v20.0/{settings.WHATSAPP_PHONE_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {
                "body": message_text
            }
        }

        async with httpx.AsyncClient() as client:
            print(f"Sending message to {phone_number}: {message_text}")
            print(f"Payload: {payload}")
            print(f"url: {whatsapp_url}")
            print(f"headers: {headers}")
            response = await client.post(whatsapp_url, headers=headers, json=payload)
            if response.status_code == 200:
                return {"status": "success"}
            else:
                return {"status": "error", "message": response.json()}
