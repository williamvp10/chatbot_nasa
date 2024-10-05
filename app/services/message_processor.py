# app/services/message_processor.py

from app.dao.chat import ChatDAO
from app.schemas.chat import ChatMessageCreate
from sqlalchemy.orm import Session
from app.agent.agent import process_message


async def process_message_from_channel(db: Session, user_id: str, message: dict, channel: str, send_response_func):
    """
    Procesa el mensaje de cualquier canal (WhatsApp, web, etc.), guarda el mensaje en la base de datos y gestiona la sesión.
    """
    # Verificar si ya existe una sesión para este usuario en el canal
    session = ChatDAO.get_session_by_user_and_channel(db, user_id, channel)
    if session is None:  # Si no hay sesión, es un nuevo usuario en este canal
        session = ChatDAO.create_session(db, user_id, channel)
    
    # Manejar el tipo de mensaje (texto o ubicación)
    if 'location' in message:
        latitude = message['location']['latitude']
        longitude = message['location']['longitude']
        message_text = f"Ubicación recibida: latitud {latitude}, longitud {longitude}"
    else:
        message_text = message.get('text', {}).get('body', '')

    # Guardar el mensaje del usuario en la base de datos
    incoming_message = ChatMessageCreate(
        sender=user_id,
        content=message_text,
        message_type="user"
    )
    ChatDAO.create_message(db, incoming_message, session_id=session.session_id)

    # Procesar el mensaje con el agente
    bot_response = process_message(message_text, session.session_id)

    # Guardar la respuesta del bot en la base de datos
    bot_message = ChatMessageCreate(
        sender="bot",
        content=bot_response,
        message_type="bot"
    )
    ChatDAO.create_message(db, bot_message, session_id=session.session_id)

    # Usar la función de respuesta que fue pasada como argumento
    await send_response_func(user_id, bot_response)


async def send_message_to_web(user_id: str, message_text: str):
    """
    Envía un mensaje de respuesta al canal web.
    """
    # Implementa la lógica para enviar la respuesta al frontend web
    pass
