from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.agent.tools.get_weather import get_weather
from app.agent.tools.get_agriculture_predictions import get_agriculture_predictions
from app.core.config import settings
from datetime import datetime

# Configuración del modelo
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL_NAME,
    temperature=0.7,
    openai_api_key=settings.OPENAI_API_KEY
)

# Agente de predicción del clima
weather_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres el asistente de predicción del clima. Proporcionas información precisa sobre el clima."
        ),
        ("placeholder", "{messages}")
    ]
)

def call_weather_assistant(state):
    return Assistant(weather_assistant_prompt | llm.bind_tools([get_weather]))(state, config={"time": datetime.now()})

# Agente de recomendaciones agrícolas
agriculture_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres el asistente de recomendaciones agrícolas. Ayudas a los usuarios a entender cómo el clima afecta sus cultivos."
        ),
        ("placeholder", "{messages}")
    ]
)

def call_agriculture_assistant(state):
    return Assistant(agriculture_assistant_prompt | llm.bind_tools([get_agriculture_predictions]))(state, config={"time": datetime.now()})
