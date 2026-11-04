"""Tests for the Open-Meteo air quality client."""

from unittest.mock import Mock, patch

import pytest
from app.modules.weather.provider.air_quality import PARAMS, fetch_air_quality


def test_request_uses_configured_air_quality_parameters():
    response = Mock()
    response.json.return_value = {
        "current": {"european_aqi": 42, "pm2_5": 12.1},
    }

    with patch("app.modules.weather.provider.air_quality.requests.get", return_value=response) as get:
        payload = fetch_air_quality()

    get.assert_called_once_with(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        params=PARAMS,
        timeout=30,
    )
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
