"""Weather API use cases backed by the existing weather package."""

from datetime import datetime
from zoneinfo import ZoneInfo

from weather.api import fetch_forecast
from weather.config import PARAMS

__all__ = ["build_weather_rainny", "fetch_forecast", "get_weather_rainny"]

_TIMEZONE = str(PARAMS["timezone"])


def _as_of_date() -> str:
    return datetime.now(ZoneInfo(_TIMEZONE)).date().isoformat()


def _day_kind(date: str, as_of: str) -> str:
    if date < as_of:
        return "past"
    if date == as_of:
        return "current"
    return "future"


def build_weather_rainny(forecast: dict, as_of: str | None = None) -> dict:
    """Shape Open-Meteo daily rain into a chart series with past/current/future kinds."""
    reference = as_of or _as_of_date()
    daily = forecast.get("daily")
    if not isinstance(daily, dict):
        raise ValueError("Response does not contain a valid 'daily' section")  # noqa: TRY004

    times = daily.get("time")
    rains = daily.get("rain_sum")
    if (
        not isinstance(times, list)
        or not isinstance(rains, list)
        or len(times) != len(rains)
    ):
        raise ValueError("Response does not contain a valid daily rain series")

    days = [
        {"date": date, "rain_sum": rain, "kind": _day_kind(date, reference)}
        for date, rain in zip(times, rains, strict=True)
    ]
    daily_units = forecast.get("daily_units")
    unit = "mm"
    if isinstance(daily_units, dict) and isinstance(daily_units.get("rain_sum"), str):
        unit = daily_units["rain_sum"]

    return {
        "location": {
            "latitude": forecast.get("latitude", PARAMS["latitude"]),
            "longitude": forecast.get("longitude", PARAMS["longitude"]),
        },
        "timezone": forecast.get("timezone", _TIMEZONE),
        "as_of": reference,
        "unit": unit,
        "days": days,
    }


def get_weather_rainny() -> dict:
    return build_weather_rainny(fetch_forecast())
