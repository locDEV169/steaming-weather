"""Routes for weather forecast resources."""

from flask import Blueprint

from app.modules.weather.api_paths import (
    API_V1_AIR_QUALITY,
    API_V1_CURRENT_WEATHER,
    API_V1_INGEST,
    API_V1_INGEST_ALL,
    API_V1_LIFESTYLE_INSIGHTS,
    API_V1_SNAPSHOTS_SLUG,
    API_V1_WEATHER,
    API_V1_WEATHER_RAINNY_FORECAST,
)
from app.modules.weather.controllers import (
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

weather_blueprint = Blueprint("weather", __name__)


@weather_blueprint.get(API_V1_WEATHER)
def get_weather():
    return get_weather_forecast()


@weather_blueprint.get(API_V1_WEATHER_RAINNY_FORECAST)
def get_weather_rainny():
    return get_weather_rainny_forecast()


@weather_blueprint.get(API_V1_AIR_QUALITY)
def get_air_quality():
    return get_weather_air_quality()


@weather_blueprint.get(API_V1_SNAPSHOTS_SLUG)
def get_snapshot(slug: str):
    return get_weather_snapshot(slug)


@weather_blueprint.post(API_V1_INGEST)
def post_ingest():
    return post_weather_ingest()


@weather_blueprint.post(API_V1_INGEST_ALL)
def post_ingest_all():
    return post_weather_ingest_all()


@weather_blueprint.get(API_V1_CURRENT_WEATHER)
def get_current_weather():
    return get_current_weather_report()


@weather_blueprint.post(API_V1_CURRENT_WEATHER)
def post_current_weather():
    return post_current_weather_report()


@weather_blueprint.post(API_V1_LIFESTYLE_INSIGHTS)
def post_lifestyle():
    return post_lifestyle_insight()


@weather_blueprint.get(API_V1_LIFESTYLE_INSIGHTS)
def get_lifestyle():
    return get_lifestyle_insight()
