# app/agent/agent.py

import os
import importlib.util
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from app.core.config import settings
from app.agent.tools.get_weather import get_weather
from app.agent.tools.get_agriculture_predictions import get_agriculture_predictions
from datetime import datetime

# Ruta al directorio de herramientas
TOOLS_DIR = os.path.join(os.path.dirname(__file__), 'tools')

# Lista para almacenar las herramientas
tools = [get_weather, get_agriculture_predictions]

# Cargar dinámicamente las herramientas desde el directorio tools
for filename in os.listdir(TOOLS_DIR):
    if filename.endswith('.py') and not filename.startswith('__'):
        module_name = filename[:-3]
        module_path = os.path.join(TOOLS_DIR, filename)

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Buscar todas las funciones decoradas con @tool en el módulo
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and hasattr(attr, 'is_langchain_tool'):
                tools.append(attr)

# Crea el ToolNode
tool_node = ToolNode(tools)

# Definir un prompt personalizado con personalidad para el agente
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres *Don Pepe*, un campesino y cientifico experto en agricultura 🌾👩‍🌾. "
            "Tu personalidad es amigable, paciente y muy detallada, siempre habla en primera persona. "
            "Tu tarea principal es ayudar a los usuarios proporcionándoles información sobre el clima, predicciones agrícolas y asistencia general en temas relacionados con la agricultura. "
            "Siempre te aseguras de que los usuarios comprendan la información que les proporcionas, usando explicaciones simples y acompañando tus mensajes con emojis para que la experiencia sea más amigable. "
            "Además, debes resaltar las palabras clave importantes en *negrita* solo con un * al inicio y otro al final. "
            "Recuerda que los usuarios pueden no tener mucha experiencia en tecnología o ciencia, así que sé clara y ofrece recomendaciones fáciles de seguir. "
            "\n\nCada vez que un usuario inicie una conversación, debes saludarlo cálidamente, presentarte como Don Pepe y mostrarle un menú con lo que puedes hacer."
            "Este menú debe incluir lo siguiente:\n\n"
            "1. *Consultar el clima actual* 🌦️\n"
            "2. *Consultar predicciones de parametros meteorologicos* 📊 como:"
            "- Temperatura a 2 metros (°C) 🌡️\n"
            "- Precipitación total (mm/día) ☔\n"
            "- Velocidad del viento a 10 metros (m/s) 💨\n"
            "- Humedad relativa a 2 metros (%) 💧"
            "\n\n🔍 *Explicaciones para los usuarios*:\n"
            "Antes de proporcionar las predicciones es necesario que le preguntes a el usuario estas tres preguntas, has pregunta por pregunta y espera que el usuario te conteste una por una," 
            "1. que cultivos tiene o que cultivos esta interesado en cultivar."
            "2. tambien pregunta si la predicción quiere la de mañana o de la semana."
            "3. Luego de que te envien los interes es necesario que les solicites la ubicación para hacer la predicción en base a su ubicación."
            "Siempre que proporciones predicciones de parametros meteorologicos*"
            "debes explicar de manera simple y con datos reales cómo estos parámetros afectan o benefician los cultivos"
            ", y al final ofrecer recomendaciones claras que los usuarios puedan seguir para cuidar sus cutivos deacuerdo al analisis. "
            "\n\n*Información actual del usuario*:\n<User>\n{user_info}\n</User>"
            "\n\n*Intereses agricolas*:\n<User_interest>\n{user_interest}\n</User_interest>"
            "\n*Hora actual*: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
)#.partial(time=datetime.now())  # Proporcionar el tiempo actual
# Clase personalizada para el asistente con personalidad
class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable
        

    def __call__(self, state: MessagesState, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            user_info = configuration.get("user_info", "Por favor, proporcione su nombre.")
            user_interest = configuration.get("user_interest", "que cultivos tienes o que quieres cultivar? ")
            time = configuration.get("time", datetime.now())
            state = {**state, "user_info": user_info, "time": time, "user_interest": user_interest}
            result = self.runnable.invoke(state)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                # Si el modelo no da una respuesta adecuada, vuelve a preguntar
                messages = state["messages"] + [("user", "Por favor, responde con una salida válida.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}

# Configura el modelo con una temperatura ajustada para generar respuestas más creativas
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL_NAME,
    temperature=0.7,  # Ajusta la temperatura para respuestas más variadas y creativas
    openai_api_key=settings.OPENAI_API_KEY
).bind_tools(tools)

# Conectar el prompt y el modelo con las herramientas
assistant_runnable = primary_assistant_prompt | llm

# Define la función que determina si continuar o no
def should_continue(state: MessagesState):
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Define la función que llama al modelo (utilizando el asistente personalizado)
def call_model(state: MessagesState):
    messages = state['messages']
    assistant = Assistant(assistant_runnable)
    response = assistant(state, config={"time": datetime.now()})
    return response

# Define un nuevo grafo
workflow = StateGraph(MessagesState)

# Añade los nodos entre los que ciclaremos
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Establece el punto de entrada como agente
workflow.add_edge(START, "agent")

# Añade un borde condicional
workflow.add_conditional_edges(
    "agent",
    should_continue,
)

# Añade un borde normal de tools a agent
workflow.add_edge("tools", 'agent')

# Inicializa la memoria para persistir el estado entre ejecuciones del grafo
checkpointer = MemorySaver()

# Compila el grafo
agent_app = workflow.compile(checkpointer=checkpointer)

# Función para procesar mensajes
def process_message(input_message: str, thread_id: str = None):
    final_state = agent_app.invoke(
        {"messages": [HumanMessage(content=input_message)]},
        config={"configurable": {"thread_id": thread_id, "user_info": "Campesino", "user_interest": " ", "time": datetime.now()}},
    )
    return final_state["messages"][-1].content