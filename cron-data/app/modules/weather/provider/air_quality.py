"""Request and validate data from the Open-Meteo Air Quality API."""

import requests

from app.modules.weather.provider.config import PARAMS as WEATHER_PARAMS

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
PARAMS = {
    "latitude": WEATHER_PARAMS["latitude"],
    "longitude": WEATHER_PARAMS["longitude"],
    "current": (
        "european_aqi,pm2_5,pm10,nitrogen_dioxide,ozone,sulphur_dioxide"
    ),
    "timezone": WEATHER_PARAMS["timezone"],
}


def fetch_air_quality() -> dict:
    response = requests.get(API_URL, params=PARAMS, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise TypeError("Response is not a valid JSON object")

    current = payload.get("current")
    if not isinstance(current, dict):
        raise ValueError("Response does not contain a valid 'current' section")  # noqa: TRY004
    if "european_aqi" not in current:
        raise ValueError("Response current section is missing european_aqi")

    return payload
