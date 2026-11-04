"""Translate weather service outcomes into HTTP responses."""

import requests
from flask import current_app, jsonify

from app.modules.weather.ingest_service import run_ingest
from app.modules.weather.repository import SupabaseConfigError
from app.modules.weather.weather_service import (
    fetch_forecast,
    get_air_quality,
    get_weather_rainny,
)


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


def get_weather_rainny_forecast():
    try:
        return jsonify(get_weather_rainny())
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


def post_weather_ingest():
    api_key = (current_app.config.get("WEATHER_API_KEY") or "").strip()
    if not api_key:
        return (
            jsonify(
                error={
                    "code": "INGEST_AUTH_REQUIRED",
                    "message": (
                        "Set WEATHER_API_KEY before using /api/v1/ingest."
                    ),
                }
            ),
            503,
        )

    supabase_url = (current_app.config.get("SUPABASE_URL") or "").strip()
    service_key = (
        current_app.config.get("SUPABASE_SERVICE_ROLE_KEY") or ""
    ).strip()
    if not supabase_url or not service_key:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_NOT_CONFIGURED",
                    "message": (
                        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
                        "must be configured."
                    ),
                }
            ),
            503,
        )

    try:
        outcome = run_ingest()
    except SupabaseConfigError:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_NOT_CONFIGURED",
                    "message": (
                        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
                        "must be configured."
                    ),
                }
            ),
            503,
        )

    if not outcome["ok"]:
        return (
            jsonify(
                error={
                    "code": "INGEST_FAILED",
                    "message": "No snapshots were updated.",
                },
                fetched_at=outcome["fetched_at"],
                results=outcome["results"],
            ),
            502,
        )

    return jsonify(outcome), 200
