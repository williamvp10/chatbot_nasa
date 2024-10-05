# app/agent/tools/get_weather.py

from langchain_core.tools import tool
import requests
from app.core.config import settings

@tool
def get_weather(city: str) -> str:
    """Obtiene el clima actual de una ciudad dada."""
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return "La clave de API para el clima no está configurada."

    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric&lang=es"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return "No se pudo obtener la información del clima."

    data = response.json()
    weather_desc = data['weather'][0]['description']
    temp = data['main']['temp']
    return f"En {city}, la temperatura es {temp}°C y el clima es {weather_desc}."

