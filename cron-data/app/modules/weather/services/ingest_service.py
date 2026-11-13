"""Fetch, shape, and persist weather snapshots to Supabase."""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from app.modules.weather.provider.air_quality import fetch_air_quality
from app.modules.weather.provider.current_weather import (
    CURRENT_WEATHER_LOCATIONS,
    resolve_current_weather_location,
)
from app.modules.weather.repositories import upsert_snapshot
from app.modules.weather.services.weather_service import (
    build_air_quality,
    build_weather_rainny,
    fetch_forecast,
)


def run_ingest_all() -> dict:
    """Ingest every registry location sequentially (partial OK per city)."""
    # Stable order: da_nang first, then remaining registry keys.
    locations = ["da_nang", *[
        key for key in CURRENT_WEATHER_LOCATIONS if key != "da_nang"
    ]]
    by_location: dict[str, dict] = {}
    for key in locations:
        by_location[key] = run_ingest(location_key=key)
    updated_locations = [
        key for key, outcome in by_location.items() if outcome.get("ok")
    ]
    return {
        "ok": len(updated_locations) > 0,
        "locations": locations,
        "updated_locations": updated_locations,
        "results_by_location": by_location,
    }


def run_ingest(location_key: str | None = None) -> dict:
    """Ingest weather, rainny, and air_quality independently (partial OK)."""
    key = resolve_current_weather_location(location_key)
    fetched_at = datetime.now(timezone.utc)  # noqa: UP017
    results: dict[str, dict] = {}

    forecast = None
    try:
        forecast = fetch_forecast(location_key=key)
        upsert_snapshot(
            "weather", forecast, fetched_at=fetched_at, location_key=key
        )
        results["weather"] = {"status": "updated"}
    except requests.Timeout:
        results["weather"] = {"status": "failed", "code": "UPSTREAM_TIMEOUT"}
    except (TypeError, ValueError):
        results["weather"] = {
            "status": "failed",
            "code": "INVALID_UPSTREAM_RESPONSE",
        }
    except requests.RequestException:
        results["weather"] = {"status": "failed", "code": "UPSTREAM_ERROR"}
    except Exception as exc:  # noqa: BLE001 — map persist errors below
        results["weather"] = _persist_or_unexpected_failure(exc)

    try:
        if forecast is None:
            forecast = fetch_forecast(location_key=key)
        rainny = build_weather_rainny(forecast)
        upsert_snapshot(
            "rainny", rainny, fetched_at=fetched_at, location_key=key
        )
        results["rainny"] = {"status": "updated"}
    except requests.Timeout:
        results["rainny"] = {"status": "failed", "code": "UPSTREAM_TIMEOUT"}
    except (TypeError, ValueError):
        results["rainny"] = {
            "status": "failed",
            "code": "INVALID_UPSTREAM_RESPONSE",
        }
    except requests.RequestException:
        results["rainny"] = {"status": "failed", "code": "UPSTREAM_ERROR"}
    except Exception as exc:  # noqa: BLE001
        results["rainny"] = _persist_or_unexpected_failure(exc)

    try:
        air_quality = build_air_quality(fetch_air_quality(location_key=key))
        upsert_snapshot(
            "air_quality", air_quality, fetched_at=fetched_at, location_key=key
        )
        results["air_quality"] = {"status": "updated"}
    except requests.Timeout:
        results["air_quality"] = {"status": "failed", "code": "UPSTREAM_TIMEOUT"}
    except (TypeError, ValueError):
        results["air_quality"] = {
            "status": "failed",
            "code": "INVALID_UPSTREAM_RESPONSE",
        }
    except requests.RequestException:
        results["air_quality"] = {"status": "failed", "code": "UPSTREAM_ERROR"}
    except Exception as exc:  # noqa: BLE001
        results["air_quality"] = _persist_or_unexpected_failure(exc)

    updated = [
        kind for kind, item in results.items() if item.get("status") == "updated"
    ]
    return {
        "ok": len(updated) > 0,
        "location_key": key,
        "fetched_at": fetched_at.isoformat(),
        "updated": updated,
        "results": results,
    }


def _persist_or_unexpected_failure(exc: Exception) -> dict:
    from app.modules.weather.repositories import (
        SupabaseConfigError,
        SupabaseWriteError,
    )

    if isinstance(exc, SupabaseConfigError):
        return {"status": "failed", "code": "SUPABASE_NOT_CONFIGURED"}
    if isinstance(exc, SupabaseWriteError):
        return {"status": "failed", "code": "SUPABASE_WRITE_ERROR"}
    return {"status": "failed", "code": "INTERNAL_ERROR"}
