"""Append one lifestyle context forecast. Does not write weather_snapshots."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

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
_CATALOG_PATH = Path(__file__).resolve().parents[1] / "lifestyle_evaluation.json"


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


def _same_hour(stored: object, stamp: object) -> bool:
    label = _floored_hour(stamp)
    if label is None or not isinstance(stored, str):
        return False
    return stored == label or stored.startswith(label)


def _hours_from_as_of(hours: list, as_of: object) -> list:
    """First 3 stored hours starting at as_of. Empty when as_of is absent."""
    for index, hour in enumerate(hours):
        if isinstance(hour, dict) and _same_hour(hour.get("time"), as_of):
            return [
                item
                for item in hours[index : index + _LAUNDRY_WINDOW_HOURS]
                if isinstance(item, dict)
            ]
    return []


def _with_wet_flag(hour: dict) -> dict:
    view = dict(hour)
    probability = _number(hour.get("precipitation_probability"))
    amount = _number(hour.get("precipitation"))
    if (probability is not None and probability >= 40) or (
        amount is not None and amount >= 0.2
    ):
        view["flag"] = "Nguy cơ ướt"
    return view


def _pop_score(window: list) -> float | None:
    if len(window) != _LAUNDRY_WINDOW_HOURS:
        return None
    total = 0.0
    for hour in window:
        probability = _number(hour.get("precipitation_probability"))
        total += 0.0 if probability is None else probability
    return total / _LAUNDRY_WINDOW_HOURS


def _car_wash(window: list) -> dict | None:
    """Mean stays the 3-hour PoP. A level matches when score_min <= mean <= score_max."""
    score = _pop_score(window)
    if score is None:
        return None
    result = {"score": score}
    matches = []
    for level in _catalog()["car_wash"]["levels"]:
        if not isinstance(level, dict):
            continue
        low = 0.0 if level.get("score_min") is None else _number(level.get("score_min"))
        high = _number(level.get("score_max"))
        if low is None or high is None:
            continue
        if low <= score <= high:
            matches.append(level)
    if len(matches) == 1 and isinstance(matches[0].get("message"), str):
        result["message"] = matches[0]["message"]
    return result


def _catalog() -> dict:
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def _laundry_verdict(window: list) -> dict:
    """Score is 100 minus the 3-hour PoP mean. The catalog row supplies the message."""
    score = _pop_score(window)
    if score is None:
        return {}
    rows = _catalog()["laundry"]["rows"]
    chosen = None
    for row in sorted(
        rows,
        key=lambda item: item["score_min"] if item.get("score_min") is not None else -1,
        reverse=True,
    ):
        low = row.get("score_min")
        if low is None or score >= low:
            chosen = row
            break
    if chosen is None:
        return {"score": score}
    return {
        "score": score,
        "dry_time": chosen["dry_time"],
        "status": chosen["status"],
        "message": chosen["message"],
    }


def shape_lifestyle_reading(row: dict) -> dict:
    """Latest stored series: 3-hour laundry window and the car-wash mean."""
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("lifestyle payload must be an object")  # noqa: TRY004
    hours = payload.get("hours")
    if not isinstance(hours, list):
        raise ValueError("lifestyle payload is missing hours")  # noqa: TRY004

    window = _hours_from_as_of(hours, payload.get("as_of"))
    return {
        "id": row.get("id"),
        "location_key": row.get("location_key"),
        "fetched_at": row.get("fetched_at"),
        "name": payload.get("name"),
        "as_of": payload.get("as_of"),
        "laundry": {
            "window_hours": _LAUNDRY_WINDOW_HOURS,
            "hours_returned": len(window),
            "hours": [_with_wet_flag(hour) for hour in window],
            **_laundry_verdict(window),
        },
        "car_wash": _car_wash(window),
    }


def read_latest_lifestyle() -> dict:
    """Read the newest row: laundry and car wash use the first 3 hours from as_of."""
    return shape_lifestyle_reading(get_latest_lifestyle_insight())
