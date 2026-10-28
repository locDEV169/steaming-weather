"""Translate weather service outcomes into HTTP responses."""

import requests
from flask import jsonify

from src.services.weather_service import fetch_forecast


def get_weather_forecast():
    try:
        return jsonify(fetch_forecast())
    except requests.Timeout:
        return (
            jsonify(
                error={
                    "code": "UPSTREAM_TIMEOUT",
                    "message": "Weather provider did not respond in time.",
                }
            ),
            504,
        )
    except (TypeError, ValueError):
        return (
            jsonify(
                error={
                    "code": "INVALID_UPSTREAM_RESPONSE",
                    "message": "Weather provider returned an invalid response.",
                }
            ),
            502,
        )
    except requests.RequestException:
        return (
            jsonify(
                error={
                    "code": "UPSTREAM_ERROR",
                    "message": "Weather provider returned an invalid response.",
                }
            ),
            502,
        )
