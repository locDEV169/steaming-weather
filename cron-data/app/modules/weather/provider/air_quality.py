"""Request and validate data from the Open-Meteo Air Quality API."""

from __future__ import annotations

import requests

from app.modules.weather.provider.config import PARAMS as WEATHER_PARAMS
from app.modules.weather.provider.current_weather import (
    CURRENT_WEATHER_LOCATIONS,
    resolve_current_weather_location,
)

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
# Default (da_nang legacy forecast point) — prefer air_quality_params_for().
PARAMS = {
    "latitude": WEATHER_PARAMS["latitude"],
    "longitude": WEATHER_PARAMS["longitude"],
    "hourly": (
        "pm10,pm2_5,uv_index"
    ),
    "current": (
        "european_aqi,pm2_5,pm10,nitrogen_dioxide,ozone,sulphur_dioxide,pm10,pm2_5,uv_index"
    ),
    "timezone": WEATHER_PARAMS["timezone"],
}


def air_quality_params_for(location_key: str | None = None) -> dict:
    """AQ query params for a known location (registry coords)."""
    key = resolve_current_weather_location(location_key)
    loc = CURRENT_WEATHER_LOCATIONS[key]
    return {
        **PARAMS,
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "timezone": loc["timezone"],
    }


def fetch_air_quality(location_key: str | None = None) -> dict:
    response = requests.get(
        API_URL, params=air_quality_params_for(location_key), timeout=30
    )
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
