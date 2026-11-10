"""Key WMO weather interpretation code bands for current-weather evaluation.

Ranges follow the product Summary of Key WMO Codes (English).
Codes outside these sets return None until an unmapped policy is defined.
"""

from __future__ import annotations

# (band_code, matcher). Order matters only for documentation; matchers are disjoint.
WMO_BANDS: tuple[tuple[str, object], ...] = (
    ("clear_cloud", range(0, 4)),
    ("fog", frozenset({45, 48})),
    ("drizzle", range(51, 58)),
    ("rain", range(61, 68)),
    ("snow", range(71, 78)),
    ("showers", range(80, 87)),
    ("thunderstorm", range(95, 100)),
)

WMO_SUMMARY: dict[str, dict[str, str]] = {
    "clear_cloud": {
        "level_en": "Clear sky, mainly clear, partly cloudy, and overcast",
        "level_vi": "Mây trắng, mây trắng nhẹ, mây trắng nặng, mây đen",
    },
    "fog": {
        "level_en": "Fog and depositing rime fog",
        "level_vi": "Sương mù, sương mù nhẹ, sương mù nặng, sương đen",
    },
    "drizzle": {
        "level_en": "Drizzle and freezing drizzle (light to dense intensities)",
        "level_vi": "Mưa phùn và mưa phùn lạnh giá (cường độ nhẹ đến dày đặc)",
    },
    "rain": {
        "level_en": "Rain and freezing rain (slight to heavy intensities)",
        "level_vi": "Mưa và mưa đá (cường độ nhẹ đến nặng)",
    },
    "snow": {
        "level_en": "Snow fall (slight to heavy) and snow grains",
        "level_vi": "Tuyết nhỏ, tuyết nhỏ nhẹ, tuyết nhỏ nặng, tuyết đen",
    },
    "showers": {
        "level_en": "Rain showers and snow showers (slight to violent/heavy)",
        "level_vi": "Mưa rào và mưa tuyết (từ nhẹ đến dữ dội/mạnh)",
    },
    "thunderstorm": {
        "level_en": "Thunderstorms (slight, moderate, or with hail)",
        "level_vi": "Dông (nhẹ, trung bình hoặc có mưa đá)",
    },
}


def _finite_weather_code(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not float(value).is_integer():
        return None
    return int(value)


def wmo_band_code(weather_code: object) -> str | None:
    """Return the Key WMO band_code, or None when the code is unmapped."""
    code = _finite_weather_code(weather_code)
    if code is None:
        return None
    for band_code, matcher in WMO_BANDS:
        if code in matcher:
            return band_code
    return None


def wmo_weather_evaluation(weather_code: object) -> dict | None:
    """Map weather_code to evaluation data, or None when missing/unmapped."""
    band_code = wmo_band_code(weather_code)
    if band_code is None:
        return None
    summary = WMO_SUMMARY[band_code]
    code = _finite_weather_code(weather_code)
    return {
        "weather_code": code,
        "band_code": band_code,
        "level_en": summary["level_en"],
        "level_vi": summary["level_vi"],
    }
