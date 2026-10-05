"""
PhytoSentinel — Service Météo
Récupère les données météo depuis OpenWeatherMap pour Guelma
et les stocke en base de données.
"""

import os
import requests
from datetime import datetime
from database import query

# Coordonnées de Guelma, Algérie
GUELMA_LAT  = 36.4619
GUELMA_LON  = 7.4285
VILLE_NOM   = "Guelma"

OWM_API_KEY = os.getenv("OWM_API_KEY", "")
OWM_URL     = "https://api.openweathermap.org/data/2.5/weather"


def fetch_weather() -> dict:
    """
    Récupère la météo depuis OpenWeatherMap.
    Si la clé API n'est pas configurée, retourne des données simulées.
    
    Returns:
        dict avec temperature, humidity, wind_speed, description, icon
    """
    if not OWM_API_KEY:
        return _get_fallback_weather()

    try:
        response = requests.get(OWM_URL, params={
            "lat":   GUELMA_LAT,
            "lon":   GUELMA_LON,
            "appid": OWM_API_KEY,
            "units": "metric",
            "lang":  "fr",
        }, timeout=10)
        response.raise_for_status()
        data = response.json()

        weather = {
            "temperature":     round(data["main"]["temp"], 1),
            "humidity":        data["main"]["humidity"],
            "wind_speed":      round(data["wind"]["speed"] * 3.6, 1),  # m/s → km/h
            "wind_direction":  _deg_to_direction(data["wind"].get("deg", 0)),
            "description":     data["weather"][0]["description"].capitalize(),
            "icon":            data["weather"][0]["icon"],
            "pressure":        data["main"]["pressure"],
            "ville":           VILLE_NOM,
        }

        # Stocker en base
        _save_weather(weather)
        print(f"[Météo] ✅ Données récupérées: {weather['temperature']}°C, {weather['humidity']}%")
        return weather

    except requests.RequestException as e:
        print(f"[Météo] ❌ Erreur API: {e}. Utilisation des dernières données.")
        return get_latest_weather() or _get_fallback_weather()


def get_latest_weather() -> dict | None:
    """Retourne la dernière entrée météo depuis la BDD."""
    return query(
        "SELECT * FROM weather_data ORDER BY fetched_at DESC LIMIT 1",
        fetch="one"
    )


def _save_weather(w: dict) -> None:
    """Insère un enregistrement météo dans la BDD."""
    query(
        """INSERT INTO weather_data 
           (temperature, humidity, wind_speed, wind_direction, description, icon, pressure, ville)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (w["temperature"], w["humidity"], w["wind_speed"],
         w["wind_direction"], w["description"], w["icon"],
         w["pressure"], w["ville"]),
        fetch="none"
    )


def _deg_to_direction(deg: float) -> str:
    """Convertit les degrés en direction cardinale."""
    directions = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    index = round(deg / 45) % 8
    return directions[index]


def _get_fallback_weather() -> dict:
    """
    Données de secours si l'API n'est pas disponible.
    Simulées pour Guelma en saison printanière.
    """
    return {
        "temperature":    24.0,
        "humidity":       72.0,
        "wind_speed":     15.0,
        "wind_direction": "N",
        "description":    "Partiellement nuageux",
        "icon":           "03d",
        "pressure":       1013.0,
        "ville":          VILLE_NOM,
    }
