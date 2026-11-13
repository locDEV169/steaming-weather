"""Translate weather service outcomes into HTTP responses."""

import requests  # noqa: I001
from flask import current_app, jsonify, request

from app.modules.weather.api_paths import (
    API_V1_CURRENT_WEATHER,
    API_V1_INGEST,
    API_V1_INGEST_ALL,
    API_V1_LIFESTYLE_INSIGHTS,
)
from app.modules.weather.repositories import (
    SNAPSHOT_KINDS,
    CurrentWeatherNotFoundError,
    LifestyleNotFoundError,
    SnapshotNotFoundError,
    SupabaseConfigError,
    SupabaseReadError,
    SupabaseWriteError,
    get_snapshot,
)
from app.modules.weather.provider.current_weather import (
    resolve_current_weather_location,
)
from app.modules.weather.provider.telegram import (
    TelegramConfigError,
    TelegramSendError,
)
from app.modules.weather.services.current_weather_service import (
    read_latest_current_weather,
    run_current_weather_report,
)
from app.modules.weather.services.ingest_service import (
    run_ingest,
    run_ingest_all,
)
from app.modules.weather.services.lifestyle_service import (
    read_latest_lifestyle,
    run_lifestyle_capture,
)
from app.modules.weather.services.weather_service import (
    fetch_forecast,
    get_air_quality,
    get_weather_rainny,
)

# URL slug → DB kind for GET {API_V1_SNAPSHOTS}/<slug>
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

    location_key, loc_error = _resolve_current_weather_location_param()
    if loc_error is not None:
        return loc_error

    try:
        return jsonify(get_snapshot(kind, location_key=location_key))
    except SupabaseConfigError:
        return _supabase_not_configured_response()
    except SnapshotNotFoundError:
        return (
            jsonify(
                error={
                    "code": "SNAPSHOT_NOT_FOUND",
                    "message": (
                        f"No snapshot found for kind '{slug}' "
                        f"location={location_key!r}."
                    ),
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
    auth_error = _missing_weather_api_key_response(API_V1_INGEST)
    if auth_error is not None:
        return auth_error

    supabase_error = _supabase_config_error_or_none()
    if supabase_error is not None:
        return supabase_error

    location_key, loc_error = _resolve_current_weather_location_param()
    if loc_error is not None:
        return loc_error

    try:
        outcome = run_ingest(location_key=location_key)
    except SupabaseConfigError:
        return _supabase_not_configured_response()

    if not outcome["ok"]:
        return (
            jsonify(
                error={
                    "code": "INGEST_FAILED",
                    "message": "No snapshots were updated.",
                },
                location_key=outcome.get("location_key", location_key),
                fetched_at=outcome["fetched_at"],
                results=outcome["results"],
            ),
            502,
        )

    return jsonify(outcome), 200


def post_weather_ingest_all():
    """Ingest snapshots for every registry location in one request."""
    auth_error = _missing_weather_api_key_response(API_V1_INGEST_ALL)
    if auth_error is not None:
        return auth_error

    supabase_error = _supabase_config_error_or_none()
    if supabase_error is not None:
        return supabase_error

    try:
        outcome = run_ingest_all()
    except SupabaseConfigError:
        return _supabase_not_configured_response()

    if not outcome["ok"]:
        return (
            jsonify(
                error={
                    "code": "INGEST_FAILED",
                    "message": "No snapshots were updated for any location.",
                },
                locations=outcome.get("locations", []),
                updated_locations=outcome.get("updated_locations", []),
                results_by_location=outcome.get("results_by_location", {}),
            ),
            502,
        )

    return jsonify(outcome), 200


def post_lifestyle_insight():
    """Store one lifestyle context row in lifestyle_insights only."""
    auth_error = _missing_weather_api_key_response(API_V1_LIFESTYLE_INSIGHTS)
    if auth_error is not None:
        return auth_error

    supabase_error = _supabase_config_error_or_none()
    if supabase_error is not None:
        return supabase_error

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
        return _supabase_not_configured_response()
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


def _supabase_not_configured_response():
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


def _supabase_config_error_or_none():
    """Return 503 response if Supabase env is missing; else None."""
    url = (current_app.config.get("SUPABASE_URL") or "").strip()
    key = (current_app.config.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    if not url or not key:
        return _supabase_not_configured_response()
    return None


def _missing_weather_api_key_response(route_path: str):
    """Return 503 if WEATHER_API_KEY is unset; else None."""
    api_key = (current_app.config.get("WEATHER_API_KEY") or "").strip()
    if not api_key:
        return (
            jsonify(
                error={
                    "code": "INGEST_AUTH_REQUIRED",
                    "message": f"Set WEATHER_API_KEY before using {route_path}.",
                }
            ),
            503,
        )
    return None


def _resolve_current_weather_location_param():
    """Parse ?location= query param. Returns (key, error_response)."""
    raw = request.args.get("location")
    try:
        return resolve_current_weather_location(raw), None
    except ValueError:
        return None, (
            jsonify(
                error={
                    "code": "INVALID_LOCATION",
                    "message": (
                        "location must be one of: da_nang, sai_gon "
                        "(default da_nang when omitted)."
                    ),
                }
            ),
            400,
        )


def get_current_weather_report():
    """Return the latest stored current_weather row. No Telegram side effects."""
    location_key, error = _resolve_current_weather_location_param()
    if error is not None:
        return error
    try:
        return jsonify(read_latest_current_weather(location_key=location_key)), 200
    except CurrentWeatherNotFoundError:
        return (
            jsonify(
                error={
                    "code": "CURRENT_WEATHER_NOT_FOUND",
                    "message": "No current weather has been stored yet.",
                }
            ),
            404,
        )
    except SupabaseConfigError:
        return _supabase_not_configured_response()
    except SupabaseReadError:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_READ_ERROR",
                    "message": "Failed to read current weather from Supabase.",
                }
            ),
            502,
        )


def post_current_weather_report():
    """Fetch current weather, insert current_weather, notify Telegram."""
    location_key, error = _resolve_current_weather_location_param()
    if error is not None:
        return error

    auth_error = _missing_weather_api_key_response(API_V1_CURRENT_WEATHER)
    if auth_error is not None:
        return auth_error

    supabase_error = _supabase_config_error_or_none()
    if supabase_error is not None:
        return supabase_error

    bot_token = (current_app.config.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (current_app.config.get("TELEGRAM_CHAT_ID") or "").strip()
    if not bot_token or not chat_id:
        return (
            jsonify(
                error={
                    "code": "TELEGRAM_NOT_CONFIGURED",
                    "message": (
                        "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be configured."
                    ),
                }
            ),
            503,
        )

    try:
        return jsonify(run_current_weather_report(location_key=location_key)), 200
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
        return _supabase_not_configured_response()
    except SupabaseWriteError:
        return (
            jsonify(
                error={
                    "code": "SUPABASE_WRITE_ERROR",
                    "message": "Failed to upsert current weather into Supabase.",
                }
            ),
            502,
        )
    except TelegramConfigError:
        return (
            jsonify(
                error={
                    "code": "TELEGRAM_NOT_CONFIGURED",
                    "message": (
                        "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be configured."
                    ),
                }
            ),
            503,
        )
    except TelegramSendError:
        return (
            jsonify(
                error={
                    "code": "TELEGRAM_SEND_ERROR",
                    "message": "Failed to send Telegram notification.",
                }
            ),
            502,
        )


def get_lifestyle_insight():
    """Return the newest row: 3 hours from as_of, the laundry message, and the car-wash mean."""
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
        return _supabase_not_configured_response()
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
