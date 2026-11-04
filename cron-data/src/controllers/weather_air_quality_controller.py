"""Translate air quality service outcomes into HTTP responses."""

import requests
from flask import jsonify

from src.services.weather_service import get_air_quality


def get_weather_air_quality():
    try:
        return jsonify(get_air_quality())
    except requests.Timeout:
        return (
            jsonify(
                error={
                    "code": "UPSTREAM_TIMEOUT",
                    "message": "Air quality provider did not respond in time.",
                }
            ),
            504,
        )
    except (TypeError, ValueError):
        return (
            jsonify(
                error={
                    "code": "INVALID_UPSTREAM_RESPONSE",
                    "message": "Air quality provider returned an invalid response.",
                }
            ),
            502,
        )
    except requests.RequestException:
        return (
            jsonify(
                error={
                    "code": "UPSTREAM_ERROR",
                    "message": "Air quality provider returned an invalid response.",
                }
            ),
            502,
        )
