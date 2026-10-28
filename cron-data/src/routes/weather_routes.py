"""Routes for weather forecast resources."""

from flask import Blueprint

from src.controllers.weather_controller import get_weather_forecast

weather_blueprint = Blueprint("weather", __name__)


@weather_blueprint.get("/api/v1/weather")
def get_weather():
    return get_weather_forecast()
