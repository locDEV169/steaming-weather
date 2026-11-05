"""Unit tests for repository.get_snapshot."""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from app.modules.weather.repositories.snapshots import (
    SnapshotNotFoundError,
    SupabaseReadError,
    get_latest_lifestyle_insight,
    get_snapshot,
)


@pytest.fixture
def app_ctx():
    app = Flask(__name__)
    app.config.update(
        {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "SUPABASE_LOCATION_KEY": "da_nang",
        }
    )
    with app.app_context():
        yield app


def test_get_snapshot_returns_payload(app_ctx):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = [
        {
            "location_key": "da_nang",
            "kind": "weather",
            "payload": {"current": {"temperature_2m": 26.0}},
            "fetched_at": "2026-11-04T06:00:00+00:00",
        }
    ]

    with patch(
        "app.modules.weather.repositories.snapshots.requests.get",
        return_value=response,
    ) as get:
        payload = get_snapshot("weather")

    assert payload == {"current": {"temperature_2m": 26.0}}
    get.assert_called_once()
    args, kwargs = get.call_args
    assert args[0] == "https://example.supabase.co/rest/v1/weather_snapshots"
    assert kwargs["params"]["location_key"] == "eq.da_nang"
    assert kwargs["params"]["kind"] == "eq.weather"


def test_get_snapshot_not_found(app_ctx):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = []

    with patch(
        "app.modules.weather.repositories.snapshots.requests.get",
        return_value=response,
    ):
        with pytest.raises(SnapshotNotFoundError):
            get_snapshot("rainny")


def test_get_snapshot_http_error(app_ctx):
    response = MagicMock()
    response.status_code = 401
    response.json.return_value = {"message": "JWT"}

    with patch(
        "app.modules.weather.repositories.snapshots.requests.get",
        return_value=response,
    ):
        with pytest.raises(SupabaseReadError, match="HTTP 401"):
            get_snapshot("weather")


def test_get_snapshot_rejects_unknown_kind(app_ctx):
    with pytest.raises(ValueError, match="Unsupported snapshot kind"):
        get_snapshot("nope")


def test_latest_lifestyle_orders_by_fetched_at(app_ctx):
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = [
        {
            "id": 3,
            "location_key": "da_nang",
            "payload": {"hours": []},
            "fetched_at": "2026-11-05T04:00:00+00:00",
        }
    ]

    with patch(
        "app.modules.weather.repositories.snapshots.requests.get",
        return_value=response,
    ) as get:
        row = get_latest_lifestyle_insight()

    assert row["id"] == 3
    args, kwargs = get.call_args
    assert args[0] == "https://example.supabase.co/rest/v1/lifestyle_insights"
    assert kwargs["params"]["order"] == "fetched_at.desc"
    assert kwargs["params"]["limit"] == "1"
