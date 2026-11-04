"""Routes for weather forecast resources."""

from flask import Blueprint

from app.modules.weather.controllers import (
    get_weather_air_quality,
    get_weather_forecast,
    get_weather_rainny_forecast,
    get_weather_snapshot,
    post_weather_ingest,
)

weather_blueprint = Blueprint("weather", __name__)


@weather_blueprint.get("/api/v1/weather")
def get_weather():
    return get_weather_forecast()


@weather_blueprint.get("/api/v1/weather-rainny-forecast")
def get_weather_rainny():
    return get_weather_rainny_forecast()


@weather_blueprint.get("/api/v1/air-quality")
def get_air_quality():
    return get_weather_air_quality()


@weather_blueprint.get("/api/v1/snapshots/<slug>")
def get_snapshot(slug: str):
    return get_weather_snapshot(slug)


@weather_blueprint.post("/api/v1/ingest")
def post_ingest():
    return post_weather_ingest()
