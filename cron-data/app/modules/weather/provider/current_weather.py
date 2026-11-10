"""Request Open-Meteo current weather only (Da Nang curl params)."""

from __future__ import annotations

import requests

from app.modules.weather.provider.config import API_URL

# User-specified current-weather curl. Does not change shared PARAMS.
CURRENT_WEATHER_PARAMS = {
    "latitude": 16.047079,
    "longitude": 108.22,
    "current": (
        "is_day,apparent_temperature,relative_humidity_2m,weather_code,"
        "temperature_2m,cloud_cover,showers,wind_speed_10m,rain,wind_gusts_10m"
    ),
    "timezone": "Asia/Bangkok",
}


def fetch_current_weather() -> dict:
    response = requests.get(API_URL, params=CURRENT_WEATHER_PARAMS, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise TypeError("Response is not a valid JSON object")
    current = payload.get("current")
    if not isinstance(current, dict):
        raise ValueError("Response does not contain a valid 'current' section")  # noqa: TRY004
    if "weather_code" not in current:
        raise ValueError("Response current section is missing weather_code")
    return payload
