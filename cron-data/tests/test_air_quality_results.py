"""Tests for European AQI overall band mapping."""

import pytest
from src.services.weather_service import (
    BAND_TABLE_VERSION,
    build_air_quality,
    european_aqi_band,
)


@pytest.mark.parametrize(
    ("index", "band_code"),
    [
        (0, "good"),
        (19.9, "good"),
        (20, "fair"),
        (32, "fair"),
        (39.9, "fair"),
        (40, "moderate"),
        (60, "poor"),
        (80, "very_poor"),
        (100, "very_poor"),
        (100.1, "extremely_poor"),
        (150, "extremely_poor"),
    ],
)
def test_european_aqi_band_boundaries(index, band_code):
    result = european_aqi_band(index)
    assert result["band_code"] == band_code
    assert result["index"] == index
    assert result["label_key"] == f"aqi.european.{band_code}"


def test_european_aqi_band_rejects_invalid_index():
    with pytest.raises(ValueError, match="number"):
        european_aqi_band("32")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=">="):
        european_aqi_band(-1)


def test_build_air_quality_adds_overall_results_and_summary():
    payload = {
        "latitude": 16.0544,
        "current": {"european_aqi": 32, "pm2_5": 10.9},
    }

    enriched = build_air_quality(payload)

    assert enriched["current"]["european_aqi"] == 32
    assert enriched["results"]["scale"] == "european_aqi"
    assert enriched["results"]["band_table_version"] == BAND_TABLE_VERSION
    assert enriched["results"]["overall"] == {
        "index": 32,
        "band_code": "fair",
        "label_key": "aqi.european.fair",
    }
    summary = enriched["results"]["summary"]
    assert summary["band_code"] == "fair"
    assert summary["level_en"] == "Fair"
    assert summary["level_en"] != "Good"
    assert summary["level_vi"] == "Tốt"
    assert summary["meaning_vi"]
    assert summary["meaning_en"]
    assert "us_aqi" not in enriched
    assert "us_aqi" not in enriched["current"]


@pytest.mark.parametrize(
    "index",
    [0, 20, 40, 60, 80, 100, 100.1],
)
def test_build_air_quality_summary_covers_all_bands(index):
    enriched = build_air_quality({"current": {"european_aqi": index}})
    overall = enriched["results"]["overall"]
    summary = enriched["results"]["summary"]
    assert summary["band_code"] == overall["band_code"]
    assert {"level_vi", "level_en", "meaning_vi", "meaning_en"} <= summary.keys()
