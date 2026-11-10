"""Vietnamese weather_code labels aligned with fe/src/lib/weather.js."""

from __future__ import annotations

# Same condition names as FE weatherDescriptions (label only).
WEATHER_CODE_VI: dict[int, str] = {
    0: "Nắng quang",
    1: "Ít mây",
    2: "Có mây",
    3: "Nhiều mây",
    45: "Sương mù",
    48: "Sương muối",
    51: "Mưa phùn nhẹ",
    53: "Mưa phùn",
    55: "Mưa phùn dày",
    56: "Mưa phùn đóng băng",
    57: "Mưa phùn đóng băng",
    61: "Mưa nhẹ",
    63: "Mưa vừa",
    65: "Mưa to",
    66: "Mưa đóng băng",
    67: "Mưa đóng băng",
    71: "Tuyết nhẹ",
    73: "Tuyết vừa",
    75: "Tuyết dày",
    77: "Hạt tuyết",
    80: "Mưa rào nhẹ",
    81: "Mưa rào",
    82: "Mưa rào lớn",
    85: "Mưa tuyết nhẹ",
    86: "Mưa tuyết dày",
    95: "Dông",
    96: "Dông, mưa đá nhẹ",
    99: "Dông, mưa đá",
}


def describe_weather_vi(weather_code: object) -> str:
    if isinstance(weather_code, bool) or not isinstance(weather_code, (int, float)):
        return "Chưa xác định"
    if not float(weather_code).is_integer():
        return "Chưa xác định"
    return WEATHER_CODE_VI.get(int(weather_code), "Chưa xác định")
