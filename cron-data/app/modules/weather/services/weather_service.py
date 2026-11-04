"""Weather API use cases backed by the existing weather package."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.modules.weather.provider.air_quality import fetch_air_quality
from app.modules.weather.provider.api import fetch_forecast
from app.modules.weather.provider.config import PARAMS

__all__ = [
    "BAND_TABLE_VERSION",
    "build_air_quality",
    "build_weather_rainny",
    "european_aqi_band",
    "fetch_forecast",
    "get_air_quality",
    "get_weather_rainny",
]

_TIMEZONE = str(PARAMS["timezone"])

# Open-Meteo European AQI numeric bands (EEA 2024 pollutant thresholds).
# https://open-meteo.com/en/docs/air-quality-api
# Half-open intervals [low, high); 100 is very_poor; >100 is extremely_poor.
BAND_TABLE_VERSION = "open-meteo-eea-2024"
_EAQI_BANDS: tuple[tuple[float, str, str], ...] = (
    (20.0, "good", "aqi.european.good"),
    (40.0, "fair", "aqi.european.fair"),
    (60.0, "moderate", "aqi.european.moderate"),
    (80.0, "poor", "aqi.european.poor"),
    (100.0, "very_poor", "aqi.european.very_poor"),
)

# UI copy keyed by band_code only (no second range parser).
# EN levels follow Open-Meteo names; VI levels follow product candidate table.
# Meaning text is informational EAQI band copy for UI — not clinical advice.
_EAQI_SUMMARY: dict[str, dict[str, str]] = {
    "good": {
        "level_vi": "Rất tốt",
        "level_en": "Good",
        "meaning_vi": (
            "Không khí trong lành, lý tưởng cho mọi hoạt động ngoài trời."
        ),
        "meaning_en": (
            "Air is clean and ideal for all outdoor activities."
        ),
    },
    "fair": {
        "level_vi": "Tốt",
        "level_en": "Fair",
        "meaning_vi": (
            "Không khí sạch, an toàn cho đại đa số người dân."
        ),
        "meaning_en": (
            "Air is clean and safe for the vast majority of people."
        ),
    },
    "moderate": {
        "level_vi": "Trung bình",
        "level_en": "Moderate",
        "meaning_vi": (
            "Chấp nhận được; nhóm quá nhạy cảm có thể thấy triệu chứng nhẹ."
        ),
        "meaning_en": (
            "Acceptable; very sensitive groups may notice mild symptoms."
        ),
    },
    "poor": {
        "level_vi": "Kém",
        "level_en": "Poor",
        "meaning_vi": (
            "Người nhạy cảm (hen suyễn, tim mạch, trẻ nhỏ) nên giảm "
            "vận động mạnh ngoài trời."
        ),
        "meaning_en": (
            "Sensitive people (asthma, heart conditions, young children) "
            "should reduce intense outdoor activity."
        ),
    },
    "very_poor": {
        "level_vi": "Rất kém",
        "level_en": "Very Poor",
        "meaning_vi": (
            "Mọi người bắt đầu cảm nhận tác động xấu, nên hạn chế ra ngoài."
        ),
        "meaning_en": (
            "Everyone may start feeling adverse effects; limit time outdoors."
        ),
    },
    "extremely_poor": {
        "level_vi": "Cực kỳ nguy hại",
        "level_en": "Extremely Poor",
        "meaning_vi": (
            "Tránh hoàn toàn việc vận động thể lực ngoài trời."
        ),
        "meaning_en": (
            "Avoid outdoor physical activity entirely."
        ),
    },
}


def _as_of_date() -> str:
    return datetime.now(ZoneInfo(_TIMEZONE)).date().isoformat()


def _day_kind(date: str, as_of: str) -> str:
    if date < as_of:
        return "past"
    if date == as_of:
        return "current"
    return "future"


def build_weather_rainny(forecast: dict, as_of: str | None = None) -> dict:
    """Shape Open-Meteo daily rain into a chart series with past/current/future kinds."""
    reference = as_of or _as_of_date()
    daily = forecast.get("daily")
    if not isinstance(daily, dict):
        raise ValueError("Response does not contain a valid 'daily' section")  # noqa: TRY004

    times = daily.get("time")
    rains = daily.get("rain_sum")
    if (
        not isinstance(times, list)
        or not isinstance(rains, list)
        or len(times) != len(rains)
    ):
        raise ValueError("Response does not contain a valid daily rain series")

    days = [
        {"date": date, "rain_sum": rain, "kind": _day_kind(date, reference)}
        for date, rain in zip(times, rains, strict=True)
    ]
    daily_units = forecast.get("daily_units")
    unit = "mm"
    if isinstance(daily_units, dict) and isinstance(daily_units.get("rain_sum"), str):
        unit = daily_units["rain_sum"]

    return {
        "location": {
            "latitude": forecast.get("latitude", PARAMS["latitude"]),
            "longitude": forecast.get("longitude", PARAMS["longitude"]),
        },
        "timezone": forecast.get("timezone", _TIMEZONE),
        "as_of": reference,
        "unit": unit,
        "days": days,
    }


def get_weather_rainny() -> dict:
    return build_weather_rainny(fetch_forecast())


def european_aqi_band(index: float) -> dict:
    """Map a European AQI number to band_code + label_key."""
    if not isinstance(index, (int, float)) or isinstance(index, bool):
        raise ValueError("european_aqi must be a number")  # noqa: TRY004
    if index < 0:
        raise ValueError("european_aqi must be >= 0")

    for upper, band_code, label_key in _EAQI_BANDS:
        if index < upper:
            return {
                "index": index,
                "band_code": band_code,
                "label_key": label_key,
            }
    if index <= 100:
        return {
            "index": index,
            "band_code": "very_poor",
            "label_key": "aqi.european.very_poor",
        }
    return {
        "index": index,
        "band_code": "extremely_poor",
        "label_key": "aqi.european.extremely_poor",
    }


def build_air_quality(payload: dict) -> dict:
    """Attach overall EAQI results beside the upstream air-quality payload."""
    current = payload.get("current")
    if not isinstance(current, dict):
        raise ValueError("Response does not contain a valid 'current' section")  # noqa: TRY004
    if "european_aqi" not in current:
        raise ValueError("Response current section is missing european_aqi")

    overall = european_aqi_band(current["european_aqi"])
    band_code = overall["band_code"]
    copy = _EAQI_SUMMARY[band_code]
    enriched = dict(payload)
    enriched["results"] = {
        "scale": "european_aqi",
        "band_table_version": BAND_TABLE_VERSION,
        "source": "https://open-meteo.com/en/docs/air-quality-api",
        "overall": overall,
        "summary": {
            "band_code": band_code,
            "level_vi": copy["level_vi"],
            "level_en": copy["level_en"],
            "meaning_vi": copy["meaning_vi"],
            "meaning_en": copy["meaning_en"],
        },
    }
    return enriched


def get_air_quality() -> dict:
    return build_air_quality(fetch_air_quality())
