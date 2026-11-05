"""Append one lifestyle context forecast. Does not write weather_snapshots."""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.weather.repositories import (
    get_latest_lifestyle_insight,
    insert_lifestyle_insight,
)
from app.modules.weather.services.weather_service import (
    build_lifestyle_insight,
    fetch_forecast,
)


def run_lifestyle_capture() -> dict:
    """Fetch Open-Meteo, shape the 72-hour context record, insert one history row."""
    fetched_at = datetime.now(timezone.utc)  # noqa: UP017
    insight = build_lifestyle_insight(fetch_forecast())
    saved = insert_lifestyle_insight(insight, fetched_at=fetched_at)
    return {
        "ok": True,
        "id": saved.get("id"),
        "location_key": saved["location_key"],
        "fetched_at": saved["fetched_at"],
        "as_of": insight["as_of"],
        "hours_returned": insight["hours_returned"],
    }


_LAUNDRY_WINDOW_HOURS = 3
_OUTFIT_KEYS = ("temperature_2m", "precipitation", "wind_speed_10m")


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _floored_hour(stamp: object) -> str | None:
    if not isinstance(stamp, str) or "T" not in stamp:
        return None
    date_part, time_part = stamp.split("T", 1)
    if len(time_part) < 2:
        return None
    return f"{date_part}T{time_part[:2]}:00"


def _hour_at(hours: list, stamp: object) -> dict | None:
    label = _floored_hour(stamp)
    if label is None:
        return None
    for hour in hours:
        if isinstance(hour, dict) and hour.get("time") == label:
            return hour
    return None


def shape_lifestyle_reading(row: dict) -> dict:
    """Latest stored series, 3-hour laundry window, current hour vs series min/max."""
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("lifestyle payload must be an object")  # noqa: TRY004
    hours = payload.get("hours")
    if not isinstance(hours, list):
        raise ValueError("lifestyle payload is missing hours")  # noqa: TRY004

    window = [hour for hour in hours[:_LAUNDRY_WINDOW_HOURS] if isinstance(hour, dict)]
    current = payload.get("current") if isinstance(payload.get("current"), dict) else {}
    outfit_hour = _hour_at(hours, current.get("time")) or _hour_at(hours, payload.get("as_of"))
    if outfit_hour is None and hours and isinstance(hours[0], dict):
        outfit_hour = hours[0]

    series = {}
    hour_view = {"time": outfit_hour.get("time") if outfit_hour else None}
    compared = {}
    for key in _OUTFIT_KEYS:
        values = [
            number
            for number in (
                _number(hour.get(key))
                for hour in hours
                if isinstance(hour, dict)
            )
            if number is not None
        ]
        low = min(values) if values else None
        high = max(values) if values else None
        series[key] = {"min": low, "max": high}
        current_value = _number(outfit_hour.get(key)) if outfit_hour else None
        hour_view[key] = outfit_hour.get(key) if outfit_hour else None
        if current_value is None or low is None or high is None:
            compared[key] = None
        else:
            compared[key] = {
                "minus_min": current_value - low,
                "minus_max": current_value - high,
            }
    if outfit_hour:
        hour_view["weather_code"] = outfit_hour.get("weather_code")
        hour_view["rain"] = outfit_hour.get("rain")
        hour_view["showers"] = outfit_hour.get("showers")

    return {
        "id": row.get("id"),
        "location_key": row.get("location_key"),
        "fetched_at": row.get("fetched_at"),
        "name": payload.get("name"),
        "as_of": payload.get("as_of"),
        "laundry": {
            "window_hours": _LAUNDRY_WINDOW_HOURS,
            "hours_returned": len(window),
            "hours": window,
        },
        "outfit": {
            "hour": hour_view,
            "series": series,
            "compared_to_series": compared,
        },
    }


def read_latest_lifestyle() -> dict:
    """Read the newest lifestyle row and shape laundry plus outfit context."""
    return shape_lifestyle_reading(get_latest_lifestyle_insight())
