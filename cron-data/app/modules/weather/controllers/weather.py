"""Translate weather service outcomes into HTTP responses."""

import requests
from flask import current_app, jsonify

from app.modules.weather.repositories import (
    SNAPSHOT_KINDS,
    LifestyleNotFoundError,
    SnapshotNotFoundError,
    SupabaseConfigError,
    SupabaseReadError,
    SupabaseWriteError,
    get_snapshot,
)
from app.modules.weather.services.ingest_service import run_ingest
from app.modules.weather.services.lifestyle_service import (
    read_latest_lifestyle,
    run_lifestyle_capture,
)
from app.modules.weather.services.weather_service import (
    fetch_forecast,
    get_air_quality,
    get_weather_rainny,
)

# URL slug → DB kind for GET /api/v1/snapshots/<slug>
SNAPSHOT_SLUGS = {
    "weather": "weather",
    "rainny": "rainny",
    "air-quality": "air_quality",
}


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


def get_weather_snapshot(slug: str):
    """Return stored Supabase snapshot payload for a kind slug."""
    kind = SNAPSHOT_SLUGS.get(slug)
    if kind is None or kind not in SNAPSHOT_KINDS:
        return (
            jsonify(
                error={
                    "code": "INVALID_SNAPSHOT_KIND",
                    "message": (
                        "Snapshot kind must be one of: weather, rainny, air-quality."
                    ),
                }
            ),
            400,
        )

    try:
        return jsonify(get_snapshot(kind))
    except SupabaseConfigError:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_NOT_CONFIGURED",
                    "message": (
                        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
                    ),
                }
            ),
            503,
        )
    except SnapshotNotFoundError:
        return (
            jsonify(
                error={
                    "code": "SNAPSHOT_NOT_FOUND",
                    "message": f"No snapshot found for kind '{slug}'.",
                }
            ),
            404,
        )
    except SupabaseReadError:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_READ_ERROR",
                    "message": "Failed to read snapshot from Supabase.",
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
                    "message": ("Set WEATHER_API_KEY before using /api/v1/ingest."),
                }
            ),
            503,
        )

    supabase_url = (current_app.config.get("SUPABASE_URL") or "").strip()
    service_key = (current_app.config.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not supabase_url or not service_key:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_NOT_CONFIGURED",
                    "message": (
                        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
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
                        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
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


def post_lifestyle_insight():
    """Store one lifestyle context row in lifestyle_insights only."""
    api_key = (current_app.config.get("WEATHER_API_KEY") or "").strip()
    if not api_key:
        return (
            jsonify(
                error={
                    "code": "INGEST_AUTH_REQUIRED",
                    "message": (
                        "Set WEATHER_API_KEY before using /api/v1/lifestyle-insights."
                    ),
                }
            ),
            503,
        )

    supabase_url = (current_app.config.get("SUPABASE_URL") or "").strip()
    service_key = (current_app.config.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not supabase_url or not service_key:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_NOT_CONFIGURED",
                    "message": (
                        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
                    ),
                }
            ),
            503,
        )

    try:
        return jsonify(run_lifestyle_capture()), 201
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
    except SupabaseConfigError:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_NOT_CONFIGURED",
                    "message": (
                        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
                    ),
                }
            ),
            503,
        )
    except SupabaseWriteError:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_WRITE_ERROR",
                    "message": "Failed to insert lifestyle insight into Supabase.",
                }
            ),
            502,
        )


def get_lifestyle_insight():
    """Return the newest lifestyle row: 3-hour laundry window and current-hour outfit."""
    try:
        return jsonify(read_latest_lifestyle())
    except LifestyleNotFoundError:
        return (
            jsonify(
                error={
                    "code": "LIFESTYLE_NOT_FOUND",
                    "message": "No lifestyle insight has been stored yet.",
                }
            ),
            404,
        )
    except SupabaseConfigError:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_NOT_CONFIGURED",
                    "message": (
                        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
                    ),
                }
            ),
            503,
        )
    except (SupabaseReadError, TypeError, ValueError):
        return (
            jsonify(
                error={
                    "code": "SUPABASE_READ_ERROR",
                    "message": "Failed to read lifestyle insight from Supabase.",
                }
            ),
            502,
        )
