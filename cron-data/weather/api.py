"""Request and validate data from the Open-Meteo Forecast API."""

import requests

from weather.config import API_URL, PARAMS


def fetch_forecast() -> dict:
    response = requests.get(API_URL, params=PARAMS, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise TypeError("Response is not a valid JSON object")

    for section in ("current", "hourly", "daily"):
        if not isinstance(payload.get(section), dict):
            raise ValueError(f"Response does not contain a valid '{section}' section")  # noqa: TRY004

    return payload
