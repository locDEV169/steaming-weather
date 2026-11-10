"""Request Open-Meteo current weather for a known location."""

from __future__ import annotations

import requests

from app.modules.weather.provider.config import API_URL

DEFAULT_LOCATION_KEY = "da_nang"

_CURRENT_FIELDS = (
    "is_day,apparent_temperature,relative_humidity_2m,weather_code,"
    "temperature_2m,cloud_cover,showers,wind_speed_10m,rain,wind_gusts_10m,precipitation"
)

# Closed enum for current-weather API. Coords are fixed per key.
CURRENT_WEATHER_LOCATIONS = {
    "da_nang": {
        "latitude": 16.047079,
        "longitude": 108.22,
        "timezone": "Asia/Bangkok",
        "label": "Đà Nẵng",
    },
    "sai_gon": {
        "latitude": 10.762622,
        "longitude": 106.660172,
        "timezone": "Asia/Bangkok",
        "label": "Sài Gòn",
    },
}

# Backward-compatible default params (da_nang).
CURRENT_WEATHER_PARAMS = {
    "latitude": CURRENT_WEATHER_LOCATIONS["da_nang"]["latitude"],
    "longitude": CURRENT_WEATHER_LOCATIONS["da_nang"]["longitude"],
    "current": _CURRENT_FIELDS,
    "timezone": CURRENT_WEATHER_LOCATIONS["da_nang"]["timezone"],
}


def resolve_current_weather_location(location_key: str | None = None) -> str:
    """Return a supported location_key; blank/None defaults to da_nang."""
    if location_key is None or not str(location_key).strip():
        return DEFAULT_LOCATION_KEY
    key = str(location_key).strip()
    if key not in CURRENT_WEATHER_LOCATIONS:
        raise ValueError(f"Unsupported location_key: {key!r}")
    return key


def current_weather_params_for(location_key: str = DEFAULT_LOCATION_KEY) -> dict:
    key = resolve_current_weather_location(location_key)
    loc = CURRENT_WEATHER_LOCATIONS[key]
    return {
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "current": _CURRENT_FIELDS,
        "timezone": loc["timezone"],
    }


def fetch_current_weather(location_key: str = DEFAULT_LOCATION_KEY) -> dict:
    params = current_weather_params_for(location_key)
    response = requests.get(API_URL, params=params, timeout=30)
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
