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

# Definir un prompt personalizado para el agente principal
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres *Doña Gloria*, una campesina y científica experta en agricultura 🌾👩‍🌾. "
            "Tu personalidad es amigable, paciente y muy detallada. "
            "Tu tarea principal es ayudar a los usuarios proporcionándoles información sobre el clima, predicciones agrícolas y asistencia general en temas relacionados con la agricultura. "
            "Siempre te aseguras de que los usuarios comprendan la información que les proporcionas, usando explicaciones simples y acompañando tus mensajes con emojis para que la experiencia sea más amigable. "
            "Recuerda que los usuarios pueden no tener mucha experiencia en tecnología o ciencia, así que sé clara y ofrece recomendaciones fáciles de seguir. "
            "\n\nCada vez que un usuario inicie una conversación, debes saludarlo cálidamente, presentarte como Doña Gloria y mostrarle un menú con lo que puedes hacer."
            "Este menú debe incluir lo siguiente:\n\n"
            "1. *Consultar el clima actual* 🌦️\n"
            "2. *Hacer predicciones agrícolas* 📊 sobre los siguientes parámetros importantes:"
            "\n\n- *Temperatura a 2 metros (T2M)* 🌡️\n"
            "- *Precipitación total (PRECTOT)* ☔\n"
            "- *Velocidad del viento a 10 metros (WS10M)* 💨\n"
            "- *Humedad relativa a 2 metros (RH2M)* 💧"
            "\n\nPor favor, elige una opción para continuar.",
        ),
        ("placeholder", "{messages}"),
    ]
)

# Configuración del LLM
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL_NAME,
    temperature=0.7,
    openai_api_key=settings.OPENAI_API_KEY
).bind_tools(tools)

# Flujo para preguntar sobre los cultivos y la temporalidad de la predicción
def ask_cultivos_temporalidad(state: MessagesState, config: RunnableConfig):
    return {
        "messages": [
            {
                "role": "assistant",
                "content": "¿Sobre qué cultivos te gustaría recibir recomendaciones? "
                           "Además, ¿prefieres una predicción diaria, semanal o mensual?"
            }
        ]
    }

# Flujo para preguntar por latitud, longitud y temporalidad
def ask_for_location_and_period(state: MessagesState, config: RunnableConfig):
    return {
        "messages": [
            {
                "role": "assistant",
                "content": "Por favor, proporciona la latitud y longitud de tu ubicación en formato numérico (por ejemplo, 4.6 -74.08). "
                           "Además, ¿te gustaría una predicción diaria, semanal o mensual?"
            }
        ]
    }

# Función para validar y procesar las entradas del usuario
def validate_and_process_input(user_input):
    try:
        # Separar los valores proporcionados por el usuario
        user_responses = user_input.split()
        print("user_responses" , user_responses)
        # Validar latitud y longitud (deben ser números)
        lat = float(user_responses[0])  # Intentar convertir el primer valor a float
        lon = float(user_responses[1])  # Intentar convertir el segundo valor a float

        # Validar período
        period = user_responses[2].lower()
        if period not in ["diaria", "semanal", "mensual"]:
            raise ValueError("Período inválido")

        return lat, lon, period

    except (IndexError, ValueError) as e:
        # Si ocurre un error de validación, devolver un mensaje de error
        return None, None, None, f"Error: {str(e)}. Por favor, proporciona la latitud, longitud y el período correctamente."

# Flujo para procesar la predicción y dar una recomendación
def handle_agriculture_prediction(state: MessagesState, config: RunnableConfig):
    user_input = state["messages"][-1].content  # Obtener el último mensaje del usuario

    # Validar y procesar la entrada del usuario
    lat, lon, period, error_message = validate_and_process_input(user_input)

    if error_message:
        # Si hubo un error de validación, devolver el mensaje de error al usuario
        return {
            "messages": [
                {"role": "assistant", "content": error_message}
            ]
        }

    # Definir el día para la predicción (puede ajustarse según la lógica)
    day = 1  # Asignamos un valor de día genérico, pero puedes cambiarlo según la necesidad

    # Invocar la herramienta de predicción agrícola
    result = get_agriculture_predictions.invoke({"lat": lat, "lon": lon, "day": day, "period": period}, config)

    # Interpretar los datos obtenidos
    prediction = result['messages'][-1].get('text', '')
    interpretation = (
        f"Con base en la predicción recibida, parece que tus cultivos podrían verse afectados "
        f"por {prediction}. Te recomiendo tener en cuenta las siguientes precauciones: ..."
    )
    
    return {
        "messages": [
            {"role": "assistant", "content": interpretation}
        ]
    }

# Clase personalizada para el asistente
class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: MessagesState, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)
            if not result.tool_calls and (
                not result.content or isinstance(result.content, list)
                and not result.content[0].get("text")):
                messages = state["messages"] + [("user", "Por favor, responde con una salida válida.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}
# Define la función que determina si continuar o no
def should_continue(state: MessagesState):
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END
# Conectar el modelo con el flujo del asistente
assistant_runnable = primary_assistant_prompt | llm

# Crear workflow de conversación
workflow = StateGraph(MessagesState)

# Añadir nodos para el flujo del asistente
workflow.add_node("agent", lambda state: Assistant(assistant_runnable)(state, config={"time": datetime.now()}))
workflow.add_node("tools", tool_node)  # Nodo para herramientas
workflow.add_node("ask_cultivos", ask_cultivos_temporalidad)
workflow.add_node("ask_location_and_period", ask_for_location_and_period)
workflow.add_node("handle_agriculture_prediction", handle_agriculture_prediction)

# Configurar flujo de tareas
def delegate_task(state: MessagesState):
    last_message = state["messages"][-1].content.lower()  # Acceder al atributo 'content' correctamente
    if "clima" in last_message:
        return "tools"  # Dirigir a la herramienta de clima
    elif "predicciones" in last_message or "agrícola" in last_message:
        return "ask_location_and_period"  # Pedir ubicación y período
    return END

# Establecer bordes entre los nodos
workflow.add_edge("ask_location_and_period", "handle_agriculture_prediction")
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", delegate_task)
workflow.add_conditional_edges("tools", should_continue)

# Inicializar memoria y compilar el grafo
checkpointer = MemorySaver()
agent_app = workflow.compile(checkpointer=checkpointer)

# Función para procesar mensajes con el thread_id
def process_message(input_message: str, thread_id: str = None):
    final_state = agent_app.invoke(
        {"messages": [HumanMessage(content=input_message)]},
        config={"configurable": {"thread_id": thread_id, "time": datetime.now()}}
    )
    return final_state["messages"][-1].content
