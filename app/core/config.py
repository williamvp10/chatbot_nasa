# app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "ChatBot API"
    DATABASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str = "gpt-3.5-turbo"  # Modelo por defecto
    OPENWEATHER_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    WHATSAPP_API_TOKEN: str
    WHATSAPP_PHONE_ID: str
    VERIFY_TOKEN: str


    class Config:
        env_file = ".env"

settings = Settings()
