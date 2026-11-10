"""Fetch Open-Meteo current weather, persist, and notify Telegram."""

from __future__ import annotations

from datetime import datetime, timezone

from app.modules.weather.provider.current_weather import fetch_current_weather
from app.modules.weather.provider.telegram import send_telegram_message
from app.modules.weather.repositories import (
    get_current_weather,
    insert_current_weather,
)
from app.modules.weather.utils.weather_describe import describe_weather_vi
from app.modules.weather.utils.wmo_weather_code import wmo_weather_evaluation


def read_latest_current_weather() -> dict:
    """Read the latest stored current_weather row. No fetch, insert, or Telegram."""
    return get_current_weather()


def _shape_current_weather_payload(raw: dict) -> dict:
    current = raw["current"]
    shaped = {
        "latitude": raw.get("latitude"),
        "longitude": raw.get("longitude"),
        "timezone": raw.get("timezone"),
        "current": current,
    }
    if isinstance(raw.get("current_units"), dict):
        shaped["current_units"] = raw["current_units"]
    evaluation = wmo_weather_evaluation(current.get("weather_code"))
    if evaluation is not None:
        shaped["evaluation"] = evaluation
    return shaped


def _telegram_text(payload: dict) -> str:
    current = payload.get("current")
    if not isinstance(current, dict):
        current = {}
    evaluation = payload.get("evaluation") if isinstance(payload.get("evaluation"), dict) else {}
    level = evaluation.get("level_en")
    level_vi = evaluation.get("level_vi")
    weather_desc = describe_weather_vi(current.get("weather_code"))
    rain_mm = current.get("rain", 0) or current.get("showers", 0)
    return "\n".join(
        [
            f"📍 Vị trí: {payload.get('location_key', 'Da Nang')}",
            "────────────────────────",
            f"🕒 Cập nhật lúc: {current.get('time', '—')}",
            (
                f"🌡 Nhiệt độ: {current.get('temperature_2m', '—')}°C "
                f"(Cảm giác như: {current.get('apparent_temperature', '—')}°C)"
            ),
            f"🌥 Trạng thái: {weather_desc}",
            f"💧 Độ ẩm: {current.get('relative_humidity_2m', '—')}%",
            f"☁️ Mây che phủ: {current.get('cloud_cover', '—')}%",
            f"🌧 Lượng mưa: {rain_mm} mm",
            (
                f"💨 Gió: {current.get('wind_speed_10m', '—')} km/h "
                f"(Giật: {current.get('wind_gusts_10m', '—')} km/h)"
            ),
            f"📌 Đánh giá: {level_vi or level or 'Bình thường'}",
        ]
    )


def run_current_weather_report() -> dict:
    """Fetch current weather, insert current_weather, then notify Telegram."""
    fetched_at = datetime.now(timezone.utc)  # noqa: UP017
    raw = fetch_current_weather()
    payload = _shape_current_weather_payload(raw)
    saved = insert_current_weather(payload, fetched_at=fetched_at)
    send_telegram_message(_telegram_text(payload))
    return {
        "ok": True,
        "id": saved.get("id"),
        "location_key": saved["location_key"],
        "fetched_at": saved["fetched_at"],
        "payload": payload,
    }
