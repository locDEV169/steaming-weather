"""Tests for the Open-Meteo air quality client."""

from unittest.mock import Mock, patch

import pytest
from app.modules.weather.provider.air_quality import (
    PARAMS,
    air_quality_params_for,
    fetch_air_quality,
)
from app.modules.weather.provider.current_weather import CURRENT_WEATHER_LOCATIONS


def test_request_uses_configured_air_quality_parameters():
    response = Mock()
    response.json.return_value = {
        "current": {"european_aqi": 42, "pm2_5": 12.1},
    }
    expected = air_quality_params_for("da_nang")

    with patch("app.modules.weather.provider.air_quality.requests.get", return_value=response) as get:
        payload = fetch_air_quality()

    get.assert_called_once_with(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        params=expected,
        timeout=30,
    )
    assert expected["latitude"] == CURRENT_WEATHER_LOCATIONS["da_nang"]["latitude"]
    assert expected["longitude"] == CURRENT_WEATHER_LOCATIONS["da_nang"]["longitude"]
    # Legacy module PARAMS keep the original forecast point for field lists.
    assert PARAMS["latitude"] == 16.0544
    assert PARAMS["longitude"] == 108.2022
    assert "european_aqi" in PARAMS["current"]
    assert "us_aqi" not in PARAMS["current"]
    assert payload["current"]["european_aqi"] == 42


def test_non_object_response_is_rejected():
    response = Mock()
    response.json.return_value = ["unexpected", "array"]

    with patch("app.modules.weather.provider.air_quality.requests.get", return_value=response):
        with pytest.raises(TypeError, match="not a valid JSON object"):
            fetch_air_quality()


def test_missing_current_section_is_rejected():
    response = Mock()
    response.json.return_value = {"latitude": 16.0544}

    with patch("app.modules.weather.provider.air_quality.requests.get", return_value=response):
        with pytest.raises(ValueError, match="current"):
            fetch_air_quality()


def test_missing_european_aqi_is_rejected():
    response = Mock()
    response.json.return_value = {"current": {"pm2_5": 12.1}}

    with patch("app.modules.weather.provider.air_quality.requests.get", return_value=response):
        with pytest.raises(ValueError, match="european_aqi"):
            fetch_air_quality()
