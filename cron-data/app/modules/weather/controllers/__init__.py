"""HTTP controllers for the weather module."""

from app.modules.weather.controllers.weather import (
    get_current_weather_report,
    get_lifestyle_insight,
    get_weather_air_quality,
    get_weather_forecast,
    get_weather_rainny_forecast,
    get_weather_snapshot,
    post_current_weather_report,
    post_lifestyle_insight,
    post_weather_ingest,
    post_weather_ingest_all,
)

__all__ = [
    "get_current_weather_report",
    "get_lifestyle_insight",
    "get_weather_air_quality",
    "get_weather_forecast",
    "get_weather_rainny_forecast",
    "get_weather_snapshot",
    "post_current_weather_report",
    "post_lifestyle_insight",
    "post_weather_ingest",
    "post_weather_ingest_all",
]
