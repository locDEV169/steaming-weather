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
    paths = schema_response.get_json()["paths"]
    assert "/api/v1/weather" in paths
    assert "/api/v1/weather-rainny-forecast" in paths
    assert "/api/v1/air-quality" in paths


def test_air_quality_route_returns_provider_payload_with_results(client, monkeypatch):
    payload = {
        "latitude": 16.0544,
        "longitude": 108.2022,
        "timezone": "Asia/Bangkok",
        "current": {"european_aqi": 42, "pm2_5": 12.1},
        "results": {
            "scale": "european_aqi",
            "band_table_version": "open-meteo-eea-2024",
            "source": "https://open-meteo.com/en/docs/air-quality-api",
            "overall": {
                "index": 42,
                "band_code": "moderate",
                "label_key": "aqi.european.moderate",
            },
            "summary": {
                "band_code": "moderate",
                "level_vi": "Trung bình",
                "level_en": "Moderate",
                "meaning_vi": (
                    "Chấp nhận được; nhóm quá nhạy cảm có thể thấy triệu chứng nhẹ."
                ),
                "meaning_en": (
                    "Acceptable; very sensitive groups may notice mild symptoms."
                ),
            },
        },
    }
    monkeypatch.setattr(
        "src.controllers.weather_air_quality_controller.get_air_quality",
        lambda: payload,
    )
    response = client.get("/api/v1/air-quality")

    assert response.status_code == 200
    assert response.content_type == "application/json"
    body = response.get_json()
    assert body == payload
    assert body["results"]["overall"]["band_code"] == "moderate"
    assert "us_aqi" not in body


def test_air_quality_route_maps_timeout_to_504(client, monkeypatch):
    def raise_timeout():
        raise requests.Timeout

    monkeypatch.setattr(
        "src.controllers.weather_air_quality_controller.get_air_quality",
        raise_timeout,
    )
    response = client.get("/api/v1/air-quality")

    assert response.status_code == 504
    assert response.get_json()["error"]["code"] == "UPSTREAM_TIMEOUT"


def test_air_quality_route_maps_upstream_error_to_502(client, monkeypatch):
    def raise_http_error():
        raise requests.HTTPError("sensitive upstream detail")

    monkeypatch.setattr(
        "src.controllers.weather_air_quality_controller.get_air_quality",
        raise_http_error,
    )
    response = client.get("/api/v1/air-quality")

    assert response.status_code == 502
    assert response.get_json()["error"]["code"] == "UPSTREAM_ERROR"
    assert "sensitive upstream detail" not in response.get_data(as_text=True)


def test_air_quality_route_maps_invalid_response_to_502(client, monkeypatch):
    def raise_invalid_response():
        raise ValueError("missing european_aqi")

    monkeypatch.setattr(
        "src.controllers.weather_air_quality_controller.get_air_quality",
        raise_invalid_response,
    )
    response = client.get("/api/v1/air-quality")

    assert response.status_code == 502
    assert response.get_json()["error"]["code"] == "INVALID_UPSTREAM_RESPONSE"
    assert "missing european_aqi" not in response.get_data(as_text=True)


def test_weather_rainny_route_returns_labeled_series(client, monkeypatch):
    payload = {
        "location": {"latitude": 16.0544, "longitude": 108.2022},
        "timezone": "Asia/Bangkok",
        "as_of": "2026-10-28",
        "unit": "mm",
        "days": [
            {"date": "2026-10-27", "rain_sum": 1.0, "kind": "past"},
            {"date": "2026-10-28", "rain_sum": 2.0, "kind": "current"},
            {"date": "2026-10-29", "rain_sum": 3.0, "kind": "future"},
        ],
    }
    monkeypatch.setattr(
        "src.controllers.weather_rainny_controller.get_weather_rainny",
        lambda: payload,
    )
    response = client.get("/api/v1/weather-rainny-forecast")

    assert response.status_code == 200
    assert response.get_json() == payload


def test_weather_rainny_route_maps_timeout_to_504(client, monkeypatch):
    def raise_timeout():
        raise requests.Timeout

    monkeypatch.setattr(
        "src.controllers.weather_rainny_controller.get_weather_rainny",
        raise_timeout,
    )
    response = client.get("/api/v1/weather-rainny-forecast")

    assert response.status_code == 504
    assert response.get_json()["error"]["code"] == "UPSTREAM_TIMEOUT"


def test_weather_rainny_route_maps_invalid_response_to_502(client, monkeypatch):
    def raise_invalid_response():
        raise ValueError("broken daily rain series")

    monkeypatch.setattr(
        "src.controllers.weather_rainny_controller.get_weather_rainny",
        raise_invalid_response,
    )
    response = client.get("/api/v1/weather-rainny-forecast")

    assert response.status_code == 502
    assert response.get_json()["error"]["code"] == "INVALID_UPSTREAM_RESPONSE"
    assert "broken daily rain series" not in response.get_data(as_text=True)
