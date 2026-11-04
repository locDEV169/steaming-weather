"""API tests for Supabase snapshot GET endpoints."""


def test_snapshot_requires_supabase_config(client):
    response = client.get("/api/v1/snapshots/weather")

    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "SUPABASE_NOT_CONFIGURED"


def test_snapshot_rejects_invalid_kind(client):
    app = client.application
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"

    response = client.get("/api/v1/snapshots/unknown")

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_SNAPSHOT_KIND"


def test_snapshot_weather_returns_payload(client, monkeypatch):
    app = client.application
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"
    payload = {
        "current": {"temperature_2m": 26.3},
        "hourly": {"time": ["2026-11-04T10:00"]},
        "daily": {"time": ["2026-11-04"]},
    }
    monkeypatch.setattr(
        "app.modules.weather.controllers.weather.get_snapshot",
        lambda kind: payload if kind == "weather" else {},
    )

    response = client.get("/api/v1/snapshots/weather")

    assert response.status_code == 200
    assert response.get_json() == payload


def test_snapshot_air_quality_slug_maps_to_kind(client, monkeypatch):
    app = client.application
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"
    seen: list[str] = []
    payload = {
        "current": {"european_aqi": 32},
        "results": {
            "summary": {
                "band_code": "fair",
                "level_vi": "Tốt",
                "meaning_vi": "ok",
            },
            "overall": {"index": 32},
        },
    }

    def fake_get(kind: str):
        seen.append(kind)
        return payload

    monkeypatch.setattr(
        "app.modules.weather.controllers.weather.get_snapshot",
        fake_get,
    )

    response = client.get("/api/v1/snapshots/air-quality")

    assert response.status_code == 200
    assert seen == ["air_quality"]
    assert response.get_json() == payload


def test_snapshot_not_found(client, monkeypatch):
    app = client.application
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"

    def raise_missing(_kind: str):
        from app.modules.weather.repositories.snapshots import SnapshotNotFoundError

        raise SnapshotNotFoundError("missing")

    monkeypatch.setattr(
        "app.modules.weather.controllers.weather.get_snapshot",
        raise_missing,
    )

    response = client.get("/api/v1/snapshots/rainny")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "SNAPSHOT_NOT_FOUND"


def test_snapshot_read_error(client, monkeypatch):
    app = client.application
    app.config["SUPABASE_URL"] = "https://example.supabase.co"
    app.config["SUPABASE_SERVICE_ROLE_KEY"] = "service-role"

    def raise_read(_kind: str):
        from app.modules.weather.repositories.snapshots import SupabaseReadError

        raise SupabaseReadError("boom")

    monkeypatch.setattr(
        "app.modules.weather.controllers.weather.get_snapshot",
        raise_read,
    )

    response = client.get("/api/v1/snapshots/weather")

    assert response.status_code == 502
    assert response.get_json()["error"]["code"] == "SUPABASE_READ_ERROR"
