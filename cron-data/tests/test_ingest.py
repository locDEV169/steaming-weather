"""Tests for snapshot ingest into Supabase."""

from datetime import datetime, timezone

import requests
from app.modules.weather.provider.config import PARAMS


def test_ingest_requires_api_key_configured(client):
    response = client.post("/api/v1/ingest")

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "INGEST_AUTH_REQUIRED"


def test_ingest_requires_supabase_config(client):
    app = client.application
    app.config["WEATHER_API_KEY"] = "test-key"
    app.config["SUPABASE_URL"] = ""
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = ""

    response = client.post(
        "/api/v1/ingest",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "SUPABASE_NOT_CONFIGURED"


def test_ingest_rejects_invalid_api_key(client):
    app = client.application
    app.config["WEATHER_API_KEY"] = "test-key"
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"

    response = client.post(
        "/api/v1/ingest",
        headers={"X-API-Key": "wrong"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_ingest_updates_all_kinds(client, monkeypatch):
    app = client.application
    app.config["WEATHER_API_KEY"] = "test-key"
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"
    app.config["SUPABASE_LOCATION_KEY"] = "da_nang"

    forecast = {
        "latitude": 16.0544,
        "longitude": 108.2022,
        "timezone": "Asia/Bangkok",
        "current": {"temperature_2m": 26.0},
        "hourly": {"time": ["2026-11-04T10:00"], "uv_index": [4.2]},
        "daily": {
            "time": ["2026-11-04"],
            "rain_sum": [1.5],
        },
        "daily_units": {"rain_sum": "mm"},
    }
    air_payload = {
        "latitude": 16.0544,
        "current": {
            "time": "2026-11-04T10:00",
            "european_aqi": 32,
            "pm2_5": 10.9,
            "uv_index": 4.2,
        },
        "hourly": {"time": ["2026-11-04T10:00"], "uv_index": [4.2]},
    }

    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.fetch_forecast",
        lambda: forecast,
    )
    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.fetch_air_quality",
        lambda: air_payload,
    )

    upserts: list[tuple[str, dict]] = []

    def fake_upsert(kind, payload, fetched_at=None):
        upserts.append((kind, payload))
        return {
            "location_key": "da_nang",
            "kind": kind,
            "fetched_at": (fetched_at or datetime.now(timezone.utc)).isoformat(),
        }

    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.upsert_snapshot",
        fake_upsert,
    )

    response = client.post(
        "/api/v1/ingest",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    assert set(body["updated"]) == {"weather", "rainny", "air_quality"}
    assert "lifestyle" not in body["results"]
    assert {kind for kind, _ in upserts} == {
        "weather",
        "rainny",
        "air_quality",
    }
    assert "results" in upserts[2][1] or upserts[2][0] == "air_quality"
    air_row = next(payload for kind, payload in upserts if kind == "air_quality")
    assert air_row["results"]["summary"]["band_code"] == "fair"
    assert air_row["hourly"]["uv_index"] == [4.2]
    assert air_row["results"]["uv"]["index"] == 4.2
    assert air_row["results"]["uv"]["level_vi"] == "Trung bình"
    weather_row = next(payload for kind, payload in upserts if kind == "weather")
    assert "uv_index" in PARAMS["hourly"]
    assert weather_row["hourly"]["uv_index"] == [4.2]


def test_ingest_partial_success_when_air_quality_fails(client, monkeypatch):
    app = client.application
    app.config["WEATHER_API_KEY"] = "test-key"
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"

    forecast = {
        "daily": {"time": ["2026-11-04"], "rain_sum": [0.0]},
        "daily_units": {"rain_sum": "mm"},
        "latitude": 16.0544,
        "longitude": 108.2022,
        "timezone": "Asia/Bangkok",
    }
    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.fetch_forecast",
        lambda: forecast,
    )

    def raise_timeout():
        raise requests.Timeout

    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.fetch_air_quality",
        raise_timeout,
    )
    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.upsert_snapshot",
        lambda kind, payload, fetched_at=None: {
            "kind": kind,
            "fetched_at": "2026-11-04T04:00:00+00:00",
        },
    )

    response = client.post(
        "/api/v1/ingest",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    assert "weather" in body["updated"]
    assert "rainny" in body["updated"]
    assert "air_quality" not in body["updated"]
    assert body["results"]["air_quality"]["code"] == "UPSTREAM_TIMEOUT"
    assert "lifestyle" not in body["results"]
