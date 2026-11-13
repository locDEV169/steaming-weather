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
        lambda location_key=None: forecast,
    )
    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.fetch_air_quality",
        lambda location_key=None: air_payload,
    )

    upserts: list[tuple[str, dict, str | None]] = []

    def fake_upsert(kind, payload, fetched_at=None, location_key=None):
        upserts.append((kind, payload, location_key))
        return {
            "location_key": location_key or "da_nang",
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
    assert body["location_key"] == "da_nang"
    assert set(body["updated"]) == {"weather", "rainny", "air_quality"}
    assert "lifestyle" not in body["results"]
    assert {kind for kind, _, _ in upserts} == {
        "weather",
        "rainny",
        "air_quality",
    }
    assert all(loc == "da_nang" for _, _, loc in upserts)
    assert "results" in upserts[2][1] or upserts[2][0] == "air_quality"
    air_row = next(payload for kind, payload, _ in upserts if kind == "air_quality")
    assert air_row["results"]["summary"]["band_code"] == "fair"
    assert air_row["hourly"]["uv_index"] == [4.2]
    assert air_row["results"]["uv"]["index"] == 4.2
    assert air_row["results"]["uv"]["level_vi"] == "Trung bình"
    weather_row = next(payload for kind, payload, _ in upserts if kind == "weather")
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
        lambda location_key=None: forecast,
    )

    def raise_timeout(location_key=None):
        raise requests.Timeout

    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.fetch_air_quality",
        raise_timeout,
    )
    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.upsert_snapshot",
        lambda kind, payload, fetched_at=None, location_key=None: {
            "kind": kind,
            "location_key": location_key or "da_nang",
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


def test_ingest_rejects_invalid_location(client):
    app = client.application
    app.config["WEATHER_API_KEY"] = "test-key"
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"

    response = client.post(
        "/api/v1/ingest?location=hue",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_LOCATION"


def test_ingest_sai_gon_passes_location_key(client, monkeypatch):
    app = client.application
    app.config["WEATHER_API_KEY"] = "test-key"
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"
    app.config["SUPABASE_LOCATION_KEY"] = "da_nang"

    forecast = {
        "latitude": 10.762622,
        "longitude": 106.660172,
        "timezone": "Asia/Bangkok",
        "current": {"temperature_2m": 30.0},
        "hourly": {"time": ["2026-11-04T10:00"], "uv_index": [6.0]},
        "daily": {"time": ["2026-11-04"], "rain_sum": [0.0]},
        "daily_units": {"rain_sum": "mm"},
    }
    air_payload = {
        "latitude": 10.762622,
        "current": {
            "time": "2026-11-04T10:00",
            "european_aqi": 40,
            "pm2_5": 12.0,
            "uv_index": 6.0,
        },
        "hourly": {"time": ["2026-11-04T10:00"], "uv_index": [6.0]},
    }
    seen_fetch: list[str | None] = []
    upsert_keys: list[str | None] = []

    def fake_forecast(location_key=None):
        seen_fetch.append(location_key)
        return forecast

    def fake_air(location_key=None):
        return air_payload

    def fake_upsert(kind, payload, fetched_at=None, location_key=None):
        upsert_keys.append(location_key)
        return {
            "location_key": location_key,
            "kind": kind,
            "fetched_at": "2026-11-04T04:00:00+00:00",
        }

    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.fetch_forecast",
        fake_forecast,
    )
    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.fetch_air_quality",
        fake_air,
    )
    monkeypatch.setattr(
        "app.modules.weather.services.ingest_service.upsert_snapshot",
        fake_upsert,
    )

    response = client.post(
        "/api/v1/ingest?location=sai_gon",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["location_key"] == "sai_gon"
    assert seen_fetch == ["sai_gon"]
    assert upsert_keys == ["sai_gon", "sai_gon", "sai_gon"]


def test_ingest_all_requires_api_key_configured(client):
    response = client.post("/api/v1/ingest-all")

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "INGEST_AUTH_REQUIRED"


def test_ingest_all_updates_both_locations(client, monkeypatch):
    app = client.application
    app.config["WEATHER_API_KEY"] = "test-key"
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"

    def fake_run_ingest_all():
        return {
            "ok": True,
            "locations": ["da_nang", "sai_gon"],
            "updated_locations": ["da_nang", "sai_gon"],
            "results_by_location": {
                "da_nang": {
                    "ok": True,
                    "location_key": "da_nang",
                    "updated": ["weather", "rainny", "air_quality"],
                },
                "sai_gon": {
                    "ok": True,
                    "location_key": "sai_gon",
                    "updated": ["weather", "rainny", "air_quality"],
                },
            },
        }

    monkeypatch.setattr(
        "app.modules.weather.controllers.weather.run_ingest_all",
        fake_run_ingest_all,
    )

    response = client.post(
        "/api/v1/ingest-all",
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    assert body["updated_locations"] == ["da_nang", "sai_gon"]


def test_run_ingest_all_calls_each_registry_location(monkeypatch):
    from app.modules.weather.services import ingest_service

    seen: list[str] = []

    def fake_run_ingest(location_key=None):
        seen.append(location_key)
        return {
            "ok": True,
            "location_key": location_key,
            "fetched_at": "2026-11-04T04:00:00+00:00",
            "updated": ["weather"],
            "results": {"weather": {"status": "updated"}},
        }

    monkeypatch.setattr(ingest_service, "run_ingest", fake_run_ingest)

    outcome = ingest_service.run_ingest_all()

    assert outcome["ok"] is True
    assert outcome["locations"] == ["da_nang", "sai_gon"]
    assert outcome["updated_locations"] == ["da_nang", "sai_gon"]
    assert seen == ["da_nang", "sai_gon"]
    assert set(outcome["results_by_location"]) == {"da_nang", "sai_gon"}


def test_run_ingest_all_partial_ok_when_one_city_fails(monkeypatch):
    from app.modules.weather.services import ingest_service

    def fake_run_ingest(location_key=None):
        ok = location_key == "da_nang"
        return {
            "ok": ok,
            "location_key": location_key,
            "fetched_at": "2026-11-04T04:00:00+00:00",
            "updated": ["weather"] if ok else [],
            "results": {
                "weather": (
                    {"status": "updated"}
                    if ok
                    else {"status": "failed", "code": "UPSTREAM_ERROR"}
                )
            },
        }

    monkeypatch.setattr(ingest_service, "run_ingest", fake_run_ingest)

    outcome = ingest_service.run_ingest_all()

    assert outcome["ok"] is True
    assert outcome["updated_locations"] == ["da_nang"]
    assert outcome["results_by_location"]["sai_gon"]["ok"] is False
