"""Request and validate data from the Open-Meteo Forecast API."""

from __future__ import annotations

import requests

from app.modules.weather.provider.config import API_URL, PARAMS
from app.modules.weather.provider.current_weather import (
    CURRENT_WEATHER_LOCATIONS,
    resolve_current_weather_location,
)


def forecast_params_for(location_key: str | None = None) -> dict:
    """Forecast query params for a known location (registry coords)."""
    key = resolve_current_weather_location(location_key)
    loc = CURRENT_WEATHER_LOCATIONS[key]
    return {
        **PARAMS,
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
        "timezone": loc["timezone"],
    }


def fetch_forecast(location_key: str | None = None) -> dict:
    response = requests.get(
        API_URL, params=forecast_params_for(location_key), timeout=30
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise TypeError("Response is not a valid JSON object")

    for section in ("current", "hourly", "daily"):
        if not isinstance(payload.get(section), dict):
            raise ValueError(f"Response does not contain a valid '{section}' section")  # noqa: TRY004

    return payload
