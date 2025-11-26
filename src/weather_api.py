# src/weather_api.py
import requests
from datetime import date
from typing import Dict, Any

# Códigos WMO que indican lluvia / chubascos / tormenta
WMO_RAIN_CODES = {51, 53, 55, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}


def geocode_city(city: str) -> Dict[str, Any]:
    """
    Dada una ciudad → devuelve lat, lon y timezone usando Open-Meteo.
    """
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "es"},
        timeout=10
    )
    r.raise_for_status()

    results = r.json().get("results", [])
    if not results:
        raise ValueError(f"Ciudad no encontrada: {city}")

    top = results[0]
    return {
        "name": top["name"],
        "lat": top["latitude"],
        "lon": top["longitude"],
        "timezone": top["timezone"],
    }


def get_weather(city: str, day: date) -> Dict[str, Any]:
    """
    Llama a Open-Meteo y devuelve:
      - temp_c (temperatura media del día, o día más cercano)
      - is_rainy (True/False)
      - precip_prob (0..1)
      - tmin, tmax
    """
    loc = geocode_city(city)

    params = {
        "latitude": loc["lat"],
        "longitude": loc["lon"],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "weathercode",
        ],
        "forecast_days": 16,
        "timezone": loc["timezone"],
    }

    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
    r.raise_for_status()
    data = r.json()["daily"]

    # Fechas disponibles en el forecast
    days = [date.fromisoformat(d) for d in data["time"]]

    # Elegimos el índice del día más cercano dentro del rango
    if day <= days[0]:
        idx = 0
    elif day >= days[-1]:
        idx = len(days) - 1
    else:
        idx = min(range(len(days)), key=lambda k: abs((days[k] - day).days))

    tmin = data["temperature_2m_min"][idx]
    tmax = data["temperature_2m_max"][idx]
    temp_mean = (tmin + tmax) / 2

    precip_prob = data["precipitation_probability_max"][idx] / 100.0
    precip_sum = data["precipitation_sum"][idx]

    code = data["weathercode"][idx]
    is_rainy = (code in WMO_RAIN_CODES) or (precip_prob > 0.3) or (precip_sum > 0.1)

    return {
        "temp_c": float(temp_mean),
        "is_rainy": bool(is_rainy),
        "precip_prob": float(precip_prob),
        "tmin": float(tmin),
        "tmax": float(tmax),
        "raw_code": code,
        "used_date": days[idx].isoformat(),
        "city_name": loc["name"],
    }

