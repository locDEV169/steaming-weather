"""Fetch, shape, and persist weather snapshots to Supabase."""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from app.modules.weather.provider.air_quality import fetch_air_quality
from app.modules.weather.repositories import upsert_snapshot
from app.modules.weather.services.weather_service import (
    build_air_quality,
    build_weather_rainny,
    fetch_forecast,
)


def run_ingest() -> dict:
    """Ingest weather, rainny, and air_quality independently (partial OK)."""
    fetched_at = datetime.now(timezone.utc)  # noqa: UP017
    results: dict[str, dict] = {}

    forecast = None
    try:
        forecast = fetch_forecast()
        upsert_snapshot("weather", forecast, fetched_at=fetched_at)
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
            forecast = fetch_forecast()
        rainny = build_weather_rainny(forecast)
        upsert_snapshot("rainny", rainny, fetched_at=fetched_at)
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
        air_quality = build_air_quality(fetch_air_quality())
        upsert_snapshot("air_quality", air_quality, fetched_at=fetched_at)
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
