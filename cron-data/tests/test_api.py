"""HTTP contract tests for the Flask application factory."""

import requests


def test_weather_route_returns_forecast_payload(client, monkeypatch):
    payload = {
        "current": {"temperature_2m": 26.3},
        "hourly": {"time": ["2026-10-28T10:00"]},
        "daily": {"time": ["2026-10-28"]},
    }
    monkeypatch.setattr(
        "src.controllers.weather_controller.fetch_forecast", lambda: payload
    )
    response = client.get("/api/v1/weather")

    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.get_json() == payload


def test_weather_route_maps_timeout_to_504(client, monkeypatch):
    def raise_timeout():
        raise requests.Timeout

    monkeypatch.setattr(
        "src.controllers.weather_controller.fetch_forecast", raise_timeout
    )
    response = client.get("/api/v1/weather")

    assert response.status_code == 504
    assert response.get_json()["error"]["code"] == "UPSTREAM_TIMEOUT"


def test_weather_route_maps_upstream_error_to_502(client, monkeypatch):
    def raise_http_error():
        raise requests.HTTPError("sensitive upstream detail")

    monkeypatch.setattr(
        "src.controllers.weather_controller.fetch_forecast", raise_http_error
    )
    response = client.get("/api/v1/weather")

    assert response.status_code == 502
    assert response.get_json()["error"]["code"] == "UPSTREAM_ERROR"
    assert "sensitive upstream detail" not in response.get_data(as_text=True)


def test_weather_route_maps_invalid_response_to_502(client, monkeypatch):
    def raise_invalid_response():
        raise TypeError("invalid internal response")

    monkeypatch.setattr(
        "src.controllers.weather_controller.fetch_forecast", raise_invalid_response
    )
    response = client.get("/api/v1/weather")

    assert response.status_code == 502
    assert response.get_json()["error"]["code"] == "INVALID_UPSTREAM_RESPONSE"
    assert "invalid internal response" not in response.get_data(as_text=True)


def test_swagger_docs_without_trailing_slash_redirects(client):
    response = client.get("/api/docs", follow_redirects=False)

    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["Location"].endswith("/api/docs/")


def test_swagger_docs_and_openapi_definition_are_available(client):
    docs_response = client.get("/api/docs/")
    schema_response = client.get("/static/swagger.json")

    assert docs_response.status_code == 200
    assert b"swagger-ui" in docs_response.data.lower()
    assert schema_response.status_code == 200
    assert schema_response.is_json
    assert "/api/v1/weather" in schema_response.get_json()["paths"]
