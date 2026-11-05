"""Lifestyle insight shaping: 72 hours of context, no verdict."""

from datetime import datetime, timedelta

import pytest

from app.modules.weather.services.lifestyle_service import shape_lifestyle_reading
from app.modules.weather.services.weather_service import build_lifestyle_insight


def _forecast(hours: int = 100, current_time: str = "2026-11-04T10:15") -> dict:
    start = datetime(2026, 11, 4, 0, 0)
    times = [
        (start + timedelta(hours=index)).strftime("%Y-%m-%dT%H:%M")
        for index in range(hours)
    ]

    def column(value):
        return [value] * hours

    return {
        "latitude": 16.0544,
        "longitude": 108.2022,
        "timezone": "Asia/Bangkok",
        "current": {
            "time": current_time,
            "temperature_2m": 29.3,
            "weather_code": 3,
            "precipitation": 0.0,
            "rain": 0.0,
            "showers": 0.0,
            "wind_speed_10m": 7.4,
            "wind_gusts_10m": 22.7,
        },
        "hourly": {
            "time": times,
            "temperature_2m": column(26.0),
            "weather_code": column(51),
            "precipitation_probability": column(46),
            "precipitation": column(0.1),
            "rain": column(0.0),
            "showers": column(0.1),
            "wind_speed_10m": column(5.0),
            "wind_gusts_10m": column(11.0),
        },
    }


def test_lifestyle_insight_is_72_hours_from_floored_now():
    insight = build_lifestyle_insight(_forecast())

    assert insight["name"] == "Dự báo theo ngữ cảnh hành vi"
    assert insight["name_en"] == "Lifestyle & Context-aware Insights"
    assert insight["as_of"] == "2026-11-04T10:00"
    assert insight["window_hours"] == 72
    assert insight["hours_returned"] == 72
    assert insight["hours"][0]["time"] == "2026-11-04T10:00"
    assert insight["hours"][-1]["time"] == "2026-11-07T09:00"
    assert insight["hours"][0]["showers"] == 0.1
    assert insight["current"]["wind_speed_10m"] == 7.4
    assert "verdict" not in insight


def test_lifestyle_route_inserts_without_touching_snapshots(client, monkeypatch):
    app = client.application
    app.config["WEATHER_API_KEY"] = "test-key"
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"

    monkeypatch.setattr(
        "app.modules.weather.services.lifestyle_service.fetch_forecast",
        lambda: _forecast(),
    )
    monkeypatch.setattr(
        "app.modules.weather.services.lifestyle_service.insert_lifestyle_insight",
        lambda payload, fetched_at=None: {
            "id": 7,
            "location_key": "da_nang",
            "fetched_at": "2026-11-04T04:00:00+00:00",
        },
    )
    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.upsert_snapshot",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("snapshot write")),
    )

    response = client.post(
        "/api/v1/lifestyle-insights",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["ok"] is True
    assert body["id"] == 7
    assert body["hours_returned"] == 72
    assert body["as_of"] == "2026-11-04T10:00"


def test_lifestyle_route_requires_api_key(client):
    response = client.post("/api/v1/lifestyle-insights")

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "INGEST_AUTH_REQUIRED"


def test_reading_uses_three_hours_and_current_hour():
    payload = build_lifestyle_insight(_forecast())
    payload["hours"][0]["temperature_2m"] = 30.0
    payload["hours"][1]["temperature_2m"] = 20.0
    payload["hours"][4]["temperature_2m"] = 22.0
    payload["hours"][0]["wind_speed_10m"] = 9.0

    body = shape_lifestyle_reading(
        {
            "id": 4,
            "location_key": "da_nang",
            "fetched_at": "2026-11-04T04:00:00+00:00",
            "payload": payload,
        }
    )

    laundry_times = [hour["time"] for hour in body["laundry"]["hours"]]
    assert body["laundry"]["window_hours"] == 3
    assert laundry_times == [
        "2026-11-04T10:00",
        "2026-11-04T11:00",
        "2026-11-04T12:00",
    ]
    assert body["outfit"]["hour"]["time"] == "2026-11-04T10:00"
    assert body["outfit"]["hour"]["temperature_2m"] == 30.0
    assert body["outfit"]["series"]["temperature_2m"]["min"] == 20.0
    assert body["outfit"]["series"]["temperature_2m"]["max"] == 30.0
    assert body["outfit"]["compared_to_series"]["temperature_2m"]["minus_min"] == 10.0
    assert body["outfit"]["compared_to_series"]["temperature_2m"]["minus_max"] == 0.0
    assert "verdict" not in body


def test_get_lifestyle_reads_latest_without_forecast(client, monkeypatch):
    app = client.application
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"
    payload = build_lifestyle_insight(_forecast())

    monkeypatch.setattr(
        "app.modules.weather.services.lifestyle_service.get_latest_lifestyle_insight",
        lambda: {
            "id": 9,
            "location_key": "da_nang",
            "fetched_at": "2026-11-05T04:00:00+00:00",
            "payload": payload,
        },
    )
    monkeypatch.setattr(
        "app.modules.weather.services.lifestyle_service.fetch_forecast",
        lambda: (_ for _ in ()).throw(AssertionError("forecast fetch")),
    )

    response = client.get("/api/v1/lifestyle-insights")

    assert response.status_code == 200
    body = response.get_json()
    assert body["id"] == 9
    assert body["fetched_at"] == "2026-11-05T04:00:00+00:00"
    assert body["laundry"]["hours_returned"] == 3
    assert body["outfit"]["hour"]["time"] == "2026-11-04T10:00"
    assert "verdict" not in body


def test_lifestyle_insight_rejects_missing_wind():
    forecast = _forecast()
    del forecast["hourly"]["wind_speed_10m"]

    with pytest.raises(ValueError, match="wind_speed_10m"):
        build_lifestyle_insight(forecast)
