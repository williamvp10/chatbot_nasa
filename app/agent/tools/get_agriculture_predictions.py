# app/agent/tools/get_agriculture_predictions.py

from langchain_core.tools import tool
import requests

# Mapeo de periodos en inglés a los endpoints correspondientes
PERIOD_ENDPOINTS = {
    "tomorrow": "/api/Prediction/tomorrowPrediction",
    "week": "/api/Prediction/weekPrediction",
    "month": "/api/Prediction/monthPrediction",
    "quarter": "/api/Prediction/cuarterPrediction"
}

BASE_URL = "https://nasaanalisisapi-production.up.railway.app"

@tool
def get_agriculture_predictions(lat: float, lon: float, period: str) -> str:
    """
    Obtiene predicciones del clima basadas en latitud, longitud, y el periodo de tiempo (mañana, semana, mes, trimestre).
    Retorna la predicción sin realizar ningún análisis sobre los cultivos. Obtiene predicciones de:
    - **T2M**: Temperatura a 2 metros (°C) 🌡️
    - **PRECTOT**: Precipitación total (mm/día) ☔
    - **WS10M**: Velocidad del viento a 10 metros (m/s) 💨
    - **RH2M**: Humedad relativa a 2 metros (%)
    """

    # Determinar el endpoint basado en el período en inglés
    endpoint = PERIOD_ENDPOINTS.get(period.lower())
    if not endpoint:
        return f"The period '{period}' is invalid. Valid periods are: tomorrow, week, month, quarter."

    # Construir la URL completa de la API
    url = f"{BASE_URL}{endpoint}"

    # Realizar la solicitud HTTP
    try:
        response = requests.get(url, params={"latitude": 4.8616, "longitude": -74.0321}, headers={"accept": "application/json"})
        response.raise_for_status()  # Verificar que no haya errores de HTTP
        data = response.json()
        
        # Procesar la respuesta según el formato de la API
        if period.lower() == "tomorrow":
            # La respuesta para mañana tiene 4 predicciones directas
            t2m, prectot, ws10m, rh2m = data["predictions"]
            prediction = (
                f"Prediction for tomorrow:\n"
                f"- **T2M**: {t2m:.2f}°C 🌡️\n"
                f"- **PRECTOT**: {prectot:.2f} mm ☔\n"
                f"- **WS10M**: {ws10m:.2f} m/s 💨\n"
                f"- **RH2M**: {rh2m:.2f}% 💧"
            )
        else:
            # Las respuestas para semana, mes, trimestre tienen min, max, average
            t2m = data["predictions"][0]
            prectot = data["predictions"][1]
            ws10m = data["predictions"][2]
            rh2m = data["predictions"][3]
            
            prediction = (
                f"{period.capitalize()} prediction:\n"
                f"- **T2M**: Min: {t2m['min']:.2f}°C, Max: {t2m['max']:.2f}°C, Average: {t2m['average']:.2f}°C 🌡️\n"
                f"- **PRECTOT**: Min: {prectot['min']:.2f} mm, Max: {prectot['max']:.2f} mm, Average: {prectot['average']:.2f} mm ☔\n"
                f"- **WS10M**: Min: {ws10m['min']:.2f} m/s, Max: {ws10m['max']:.2f} m/s, Average: {ws10m['average']:.2f} m/s 💨\n"
                f"- **RH2M**: Min: {rh2m['min']:.2f}%, Max: {rh2m['max']:.2f}%, Average: {rh2m['average']:.2f}% 💧"
            )

        return prediction

    except requests.exceptions.RequestException as e:
        return f"Error retrieving predictions: {str(e)}"
