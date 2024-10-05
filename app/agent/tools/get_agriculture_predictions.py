# app/agent/tools/get_agriculture_predictions.py

from langchain_core.tools import tool
import requests

@tool
def get_agriculture_predictions(lat: float, lon: float, day: str, period: str) -> str:
    """Obtiene predicciones del clima basadas en latitud, longitud, y el periodo de tiempo (día de mañana, semana, mes, tres meses).
    Retorna la predicción sin realizar ningún análisis sobre los cultivos. Obtiene predicciones de:
    - **T2M**: Temperatura a 2 metros (°C) 🌡️
    - **PRECTOT**: Precipitación total (mm/día) ☔
    - **WS10M**: Velocidad del viento a 10 metros (m/s) 💨
    - **RH2M**: Humedad relativa a 2 metros (%) """
    
    # Simular la consulta a una API de predicción agrícola (esto debería ser una llamada real en un sistema productivo)
    print(f"Predicción agrícola para lat: {lat}, lon: {lon} en {period} ({day})")
    
    # Datos de predicción simulados (debería provenir de una API real)
    prediction = "T2M: 16.25°C 🌡️ \nPRECTOT: 0.69 mm ☔\nWS10M: 3.64 m/s 💨\nRH2M: 80% 💧"
    
    return f"Predicción para {period} ({day}): {prediction}"