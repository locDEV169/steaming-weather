"""Unit tests for weather-rainny series shaping."""

import pytest
from src.services.weather_service import build_weather_rainny


def test_build_weather_rainny_labels_past_current_future():
    forecast = {
        "latitude": 16.0544,
        "longitude": 108.2022,
        "timezone": "Asia/Bangkok",
        "daily_units": {"rain_sum": "mm"},
        "daily": {
            "time": ["2026-10-27", "2026-10-28", "2026-10-29"],
            "rain_sum": [1.0, 2.0, 3.0],
        },
    }

    payload = build_weather_rainny(forecast, as_of="2026-10-28")

    assert payload["as_of"] == "2026-10-28"
    assert payload["unit"] == "mm"
    assert payload["days"] == [
        {"date": "2026-10-27", "rain_sum": 1.0, "kind": "past"},
        {"date": "2026-10-28", "rain_sum": 2.0, "kind": "current"},
        {"date": "2026-10-29", "rain_sum": 3.0, "kind": "future"},
    ]


def test_build_weather_rainny_rejects_mismatched_series():
    forecast = {
        "daily": {
            "time": ["2026-10-27", "2026-10-28"],
            "rain_sum": [1.0],
        }
    }

    with pytest.raises(ValueError, match="valid daily rain series"):
        build_weather_rainny(forecast, as_of="2026-10-28")
