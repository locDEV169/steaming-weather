"""Tests for the weather domain package."""

from unittest.mock import Mock, patch

import pytest
from weather.api import fetch_forecast
from weather.config import CURRENT_COLUMNS, DAILY_COLUMNS, HOURLY_COLUMNS, PARAMS
from weather.transform import to_frame


def test_request_uses_configured_open_meteo_parameters():
    response = Mock()
    response.json.return_value = {"current": {}, "hourly": {}, "daily": {}}

    with patch("weather.api.requests.get", return_value=response) as get:
        payload = fetch_forecast()

    get.assert_called_once_with(
        "https://api.open-meteo.com/v1/forecast",
        params=PARAMS,
        timeout=30,
    )
    assert PARAMS["latitude"] == 16.0544
    assert PARAMS["longitude"] == 108.2022
    assert PARAMS["past_days"] == 7
    assert PARAMS["forecast_days"] == 7
    assert payload["current"] == {}
    assert payload["hourly"] == {}
    assert payload["daily"] == {}


def test_non_object_response_is_rejected():
    response = Mock()
    response.json.return_value = ["unexpected", "array"]

    with patch("weather.api.requests.get", return_value=response):  # noqa: SIM117
        with pytest.raises(TypeError, match="valid JSON object"):
            fetch_forecast()


def test_current_section_becomes_one_row():
    current = {
        "time": "2026-10-28T12:00",
        "interval": 900,
        "temperature_2m": 14.2,
        "weather_code": 3,
    }

    frame = to_frame("current", current)

    assert list(frame.columns) == CURRENT_COLUMNS
    assert len(frame) == 1
    assert frame.iloc[0]["weather_code"] == 3


def test_hourly_and_daily_sections_keep_timestamp_rows():
    hourly = {
        "time": ["2026-10-28T12:00", "2026-10-28T13:00"],
        "temperature_2m": [14.2, 15.0],
        "weather_code": [3, 2],
    }
    daily = {
        "time": ["2026-10-28", "2026-10-29"],
        "weather_code": [3, 2],
        "sunrise": ["2026-10-28T07:00", "2026-10-29T07:02"],
        "rain_sum": [0.0, 1.2],
        "sunset": ["2026-10-28T17:00", "2026-10-29T16:58"],
        "temperature_2m_max": [16.0, 17.0],
        "temperature_2m_min": [8.0, 9.0],
    }

    hourly_frame = to_frame("hourly", hourly)
    daily_frame = to_frame("daily", daily)

    assert list(hourly_frame.columns) == HOURLY_COLUMNS
    assert list(daily_frame.columns) == DAILY_COLUMNS
    assert len(hourly_frame) == 2
    assert len(daily_frame) == 2
    assert hourly_frame.iloc[1]["time"] == "2026-10-28T13:00"


def test_missing_requested_field_is_rejected():
    with pytest.raises(ValueError, match="weather_code"):
        to_frame("hourly", {"time": ["2026-10-28T12:00"], "temperature_2m": [14.2]})
