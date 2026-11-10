"""Tests for Key WMO weather_code band evaluation."""

import pytest
from app.modules.weather.utils.wmo_weather_code import (
    wmo_band_code,
    wmo_weather_evaluation,
)


@pytest.mark.parametrize(
    ("code", "band_code", "level_en"),
    [
        (0, "clear_cloud", "Clear sky, mainly clear, partly cloudy, and overcast"),
        (3, "clear_cloud", "Clear sky, mainly clear, partly cloudy, and overcast"),
        (45, "fog", "Fog and depositing rime fog"),
        (48, "fog", "Fog and depositing rime fog"),
        (51, "drizzle", "Drizzle and freezing drizzle (light to dense intensities)"),
        (57, "drizzle", "Drizzle and freezing drizzle (light to dense intensities)"),
        (61, "rain", "Rain and freezing rain (slight to heavy intensities)"),
        (67, "rain", "Rain and freezing rain (slight to heavy intensities)"),
        (71, "snow", "Snow fall (slight to heavy) and snow grains"),
        (77, "snow", "Snow fall (slight to heavy) and snow grains"),
        (80, "showers", "Rain showers and snow showers (slight to violent/heavy)"),
        (86, "showers", "Rain showers and snow showers (slight to violent/heavy)"),
        (95, "thunderstorm", "Thunderstorms (slight, moderate, or with hail)"),
        (99, "thunderstorm", "Thunderstorms (slight, moderate, or with hail)"),
    ],
)
def test_wmo_weather_evaluation_bands(code, band_code, level_en):
    result = wmo_weather_evaluation(code)
    assert result["weather_code"] == code
    assert result["band_code"] == band_code
    assert result["level_en"] == level_en
    assert isinstance(result.get("level_vi"), str) and result["level_vi"]
    assert wmo_band_code(code) == band_code


@pytest.mark.parametrize("code", [4, 44, 50, 58, 70, 78, 87, 94, 100, None, "51", 51.5])
def test_wmo_weather_evaluation_unmapped_or_invalid(code):
    assert wmo_band_code(code) is None
    assert wmo_weather_evaluation(code) is None
