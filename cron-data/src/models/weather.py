"""Typed shape for the Open-Meteo forecast response."""

from typing import Any, Literal, TypedDict


class WeatherForecast(TypedDict):
    latitude: float
    longitude: float
    timezone: str
    current: dict[str, Any]
    hourly: dict[str, Any]
    daily: dict[str, Any]


RainDayKind = Literal["past", "current", "future"]


class WeatherRainnyDay(TypedDict):
    date: str
    rain_sum: float
    kind: RainDayKind


class WeatherRainnyLocation(TypedDict):
    latitude: float
    longitude: float


class WeatherRainny(TypedDict):
    location: WeatherRainnyLocation
    timezone: str
    as_of: str
    unit: str
    days: list[WeatherRainnyDay]
