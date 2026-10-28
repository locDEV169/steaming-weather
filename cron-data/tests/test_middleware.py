"""Middleware contract tests: CORS, auth, logging, global errors."""

import logging

import pytest
from src import create_app


@pytest.fixture
def auth_client():
    app = create_app({"TESTING": True, "WEATHER_API_KEY": "secret-key"})
    return app.test_client()


def test_cors_headers_on_weather_response(client, monkeypatch):
    monkeypatch.setattr(
        "src.controllers.weather_controller.fetch_forecast",
        lambda: {"current": {}, "hourly": {}, "daily": {}},
    )
    response = client.get("/api/v1/weather")

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert "X-API-Key" in response.headers["Access-Control-Allow-Headers"]


def test_cors_preflight_options(client):
    response = client.options(
        "/api/v1/weather",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 204
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert "GET" in response.headers["Access-Control-Allow-Methods"]


def test_auth_disabled_by_default(client, monkeypatch):
    monkeypatch.setattr(
        "src.controllers.weather_controller.fetch_forecast",
        lambda: {"current": {}, "hourly": {}, "daily": {}},
    )
    response = client.get("/api/v1/weather")
    assert response.status_code == 200


def test_auth_rejects_missing_api_key(auth_client):
    response = auth_client.get("/api/v1/weather")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_auth_accepts_x_api_key(auth_client, monkeypatch):
    monkeypatch.setattr(
        "src.controllers.weather_controller.fetch_forecast",
        lambda: {"current": {}, "hourly": {}, "daily": {}},
    )
    response = auth_client.get(
        "/api/v1/weather", headers={"X-API-Key": "secret-key"}
    )
    assert response.status_code == 200


def test_auth_accepts_bearer_token(auth_client, monkeypatch):
    monkeypatch.setattr(
        "src.controllers.weather_controller.fetch_forecast",
        lambda: {"current": {}, "hourly": {}, "daily": {}},
    )
    response = auth_client.get(
        "/api/v1/weather", headers={"Authorization": "Bearer secret-key"}
    )
    assert response.status_code == 200


def test_auth_does_not_block_swagger_docs(auth_client):
    response = auth_client.get("/api/docs/")
    assert response.status_code == 200


def test_not_found_returns_json_error(client):
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


def test_unhandled_exception_returns_json_without_internals():
    app = create_app({"TESTING": True, "PROPAGATE_EXCEPTIONS": False})

    def boom():
        raise RuntimeError("sensitive internal detail")

    app.view_functions["weather.get_weather"] = boom
    response = app.test_client().get("/api/v1/weather")

    assert response.status_code == 500
    body = response.get_json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "sensitive internal detail" not in response.get_data(as_text=True)


def test_request_logging_emits_info(client, monkeypatch, caplog):
    monkeypatch.setattr(
        "src.controllers.weather_controller.fetch_forecast",
        lambda: {"current": {}, "hourly": {}, "daily": {}},
    )
    with caplog.at_level(logging.INFO, logger="weather.api"):
        response = client.get("/api/v1/weather")

    assert response.status_code == 200
    assert any(
        "GET" in record.getMessage() and "/api/v1/weather" in record.getMessage()
        for record in caplog.records
    )
