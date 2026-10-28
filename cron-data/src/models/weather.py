"""Typed shape for the Open-Meteo forecast response."""

from typing import Any, TypedDict


class WeatherForecast(TypedDict):
    latitude: float
    longitude: float
    timezone: str
    current: dict[str, Any]
    hourly: dict[str, Any]
    daily: dict[str, Any]
