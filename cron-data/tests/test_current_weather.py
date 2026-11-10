"""Current weather fetch, persist, Telegram notify, and WMO evaluation."""

from unittest.mock import patch

from app import create_app
from app.modules.weather.provider.current_weather import (
    CURRENT_WEATHER_PARAMS,
    current_weather_params_for,
    resolve_current_weather_location,
)
from app.modules.weather.repositories import CurrentWeatherNotFoundError
from app.modules.weather.services.current_weather_service import (
    _shape_current_weather_payload,
    _telegram_text,
    run_current_weather_report,
)


def _open_meteo_current(weather_code: int = 51) -> dict:
    return {
        "latitude": 16.047079,
        "longitude": 108.22,
        "timezone": "Asia/Bangkok",
        "current_units": {"temperature_2m": "°C"},
        "current": {
            "time": "2026-11-10T11:00",
            "interval": 900,
            "is_day": 1,
            "apparent_temperature": 33.1,
            "relative_humidity_2m": 78,
            "weather_code": weather_code,
            "temperature_2m": 29.4,
            "cloud_cover": 88,
            "showers": 0.0,
            "wind_speed_10m": 6.2,
            "rain": 0.1,
            "wind_gusts_10m": 12.0,
        },
    }


def test_shape_adds_wmo_evaluation():
    shaped = _shape_current_weather_payload(_open_meteo_current(51))
    assert shaped["evaluation"]["weather_code"] == 51
    assert shaped["evaluation"]["band_code"] == "drizzle"
    assert (
        shaped["evaluation"]["level_en"]
        == "Drizzle and freezing drizzle (light to dense intensities)"
    )
    assert isinstance(shaped["evaluation"].get("level_vi"), str)
    assert shaped["current"]["cloud_cover"] == 88
    assert shaped["current_units"]["temperature_2m"] == "°C"


def test_shape_omits_evaluation_when_unmapped():
    shaped = _shape_current_weather_payload(_open_meteo_current(4))
    assert "evaluation" not in shaped


def test_telegram_text_uses_vietnamese_layout():
    shaped = _shape_current_weather_payload(_open_meteo_current(51))
    text = _telegram_text(shaped, location_key="da_nang")
    assert "📍 Vị trí: Đà Nẵng" in text
    assert "🕒 Cập nhật lúc: 2026-11-10T11:00" in text
    assert "🌡 Nhiệt độ: 29.4°C (Cảm giác như: 33.1°C)" in text
    assert "🌥 Trạng thái: Mưa phùn nhẹ" in text
    assert "💧 Độ ẩm: 78%" in text
    assert "☁️ Mây che phủ: 88%" in text
    assert "🌧 Lượng mưa: 0.1 mm" in text
    assert "💨 Gió: 6.2 km/h (Giật: 12.0 km/h)" in text
    assert text.split("📌 Đánh giá: ", 1)[1]


def test_resolve_location_defaults_and_rejects_unknown():
    assert resolve_current_weather_location(None) == "da_nang"
    assert resolve_current_weather_location("") == "da_nang"
    assert resolve_current_weather_location("sai_gon") == "sai_gon"
    try:
        resolve_current_weather_location("hue")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_sai_gon_coords():
    params = current_weather_params_for("sai_gon")
    assert params["latitude"] == 10.762622
    assert params["longitude"] == 106.660172
    assert params["timezone"] == "Asia/Bangkok"


@patch(
    "app.modules.weather.services.current_weather_service.send_telegram_message"
)
@patch(
    "app.modules.weather.services.current_weather_service.insert_current_weather",
    return_value={
        "id": 1,
        "location_key": "da_nang",
        "fetched_at": "2026-11-10T04:00:00+00:00",
    },
)
@patch(
    "app.modules.weather.services.current_weather_service.fetch_current_weather",
    return_value=_open_meteo_current(51),
)
def test_run_current_weather_report_persists_then_notifies(
    mock_fetch, mock_insert, mock_telegram
):
    app = create_app({"TESTING": True})
    with app.app_context():
        outcome = run_current_weather_report()

    assert outcome["ok"] is True
    assert outcome["id"] == 1
    assert outcome["location_key"] == "da_nang"
    assert outcome["payload"]["evaluation"]["band_code"] == "drizzle"
    mock_fetch.assert_called_once_with(location_key="da_nang")
    mock_insert.assert_called_once()
    assert mock_insert.call_args.kwargs["location_key"] == "da_nang"
    mock_telegram.assert_called_once()
    message = mock_telegram.call_args.args[0]
    assert "📍 Vị trí: Đà Nẵng" in message
    assert "🕒 Cập nhật lúc:" in message
    assert "📌 Đánh giá:" in message


@patch(
    "app.modules.weather.services.current_weather_service.send_telegram_message"
)
@patch(
    "app.modules.weather.services.current_weather_service.insert_current_weather",
    return_value={
        "id": 2,
        "location_key": "sai_gon",
        "fetched_at": "2026-11-10T04:00:00+00:00",
    },
)
@patch(
    "app.modules.weather.services.current_weather_service.fetch_current_weather",
    return_value=_open_meteo_current(51),
)
def test_run_current_weather_report_sai_gon(
    mock_fetch, mock_insert, mock_telegram
):
    app = create_app({"TESTING": True})
    with app.app_context():
        outcome = run_current_weather_report(location_key="sai_gon")

    assert outcome["location_key"] == "sai_gon"
    mock_fetch.assert_called_once_with(location_key="sai_gon")
    assert mock_insert.call_args.kwargs["location_key"] == "sai_gon"
    assert "📍 Vị trí: Sài Gòn" in mock_telegram.call_args.args[0]


def test_current_weather_params_match_user_curl():
    assert CURRENT_WEATHER_PARAMS["latitude"] == 16.047079
    assert CURRENT_WEATHER_PARAMS["longitude"] == 108.22
    assert "cloud_cover" in CURRENT_WEATHER_PARAMS["current"]
    assert "precipitation" in CURRENT_WEATHER_PARAMS["current"]
    assert CURRENT_WEATHER_PARAMS["timezone"] == "Asia/Bangkok"


def test_get_current_weather_not_found_when_empty():
    app = create_app(
        {
            "TESTING": True,
            "WEATHER_API_KEY": "",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
        }
    )
    client = app.test_client()
    with patch(
        "app.modules.weather.controllers.weather.read_latest_current_weather",
        side_effect=CurrentWeatherNotFoundError("missing"),
    ):
        response = client.get("/api/v1/current-weather")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "CURRENT_WEATHER_NOT_FOUND"


def test_get_current_weather_invalid_location():
    app = create_app(
        {
            "TESTING": True,
            "WEATHER_API_KEY": "",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
        }
    )
    client = app.test_client()
    response = client.get("/api/v1/current-weather?location=hue")
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_LOCATION"


@patch(
    "app.modules.weather.controllers.weather.read_latest_current_weather",
    return_value={
        "location_key": "da_nang",
        "fetched_at": "2026-11-10T04:00:00+00:00",
        "payload": {"current": {"weather_code": 51}},
    },
)
def test_get_current_weather_returns_stored_row(mock_read):
    app = create_app(
        {
            "TESTING": True,
            "WEATHER_API_KEY": "",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
        }
    )
    client = app.test_client()
    response = client.get("/api/v1/current-weather")
    assert response.status_code == 200
    body = response.get_json()
    assert body["location_key"] == "da_nang"
    assert body["payload"]["current"]["weather_code"] == 51
    mock_read.assert_called_once_with(location_key="da_nang")


@patch(
    "app.modules.weather.controllers.weather.read_latest_current_weather",
    return_value={
        "location_key": "sai_gon",
        "fetched_at": "2026-11-10T04:00:00+00:00",
        "payload": {"current": {"weather_code": 51}},
    },
)
def test_get_current_weather_sai_gon_param(mock_read):
    app = create_app(
        {
            "TESTING": True,
            "WEATHER_API_KEY": "",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
        }
    )
    client = app.test_client()
    response = client.get("/api/v1/current-weather?location=sai_gon")
    assert response.status_code == 200
    assert response.get_json()["location_key"] == "sai_gon"
    mock_read.assert_called_once_with(location_key="sai_gon")


def test_post_current_weather_requires_api_key(client):
    response = client.post("/api/v1/current-weather")
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "INGEST_AUTH_REQUIRED"


def test_post_current_weather_invalid_location():
    app = create_app(
        {
            "TESTING": True,
            "WEATHER_API_KEY": "local-key",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TELEGRAM_BOT_TOKEN": "bot-token",
            "TELEGRAM_CHAT_ID": "12345",
        }
    )
    client = app.test_client()
    response = client.post(
        "/api/v1/current-weather?location=hue",
        headers={"X-API-Key": "local-key"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_LOCATION"


def test_post_current_weather_requires_telegram_when_supabase_set():
    app = create_app(
        {
            "TESTING": True,
            "WEATHER_API_KEY": "local-key",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TELEGRAM_BOT_TOKEN": "",
            "TELEGRAM_CHAT_ID": "",
        }
    )
    client = app.test_client()
    response = client.post(
        "/api/v1/current-weather",
        headers={"X-API-Key": "local-key"},
    )
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "TELEGRAM_NOT_CONFIGURED"


@patch(
    "app.modules.weather.controllers.weather.run_current_weather_report",
    return_value={
        "ok": True,
        "location_key": "da_nang",
        "fetched_at": "2026-11-10T04:00:00+00:00",
        "payload": {"current": {"weather_code": 51}},
    },
)
def test_post_current_weather_ok(mock_run):
    app = create_app(
        {
            "TESTING": True,
            "WEATHER_API_KEY": "local-key",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TELEGRAM_BOT_TOKEN": "bot-token",
            "TELEGRAM_CHAT_ID": "12345",
        }
    )
    client = app.test_client()
    response = client.post(
        "/api/v1/current-weather",
        headers={"X-API-Key": "local-key"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["ok"] is True
    assert body["location_key"] == "da_nang"
    mock_run.assert_called_once_with(location_key="da_nang")


@patch(
    "app.modules.weather.controllers.weather.run_current_weather_report",
    return_value={
        "ok": True,
        "location_key": "sai_gon",
        "fetched_at": "2026-11-10T04:00:00+00:00",
        "payload": {"current": {"weather_code": 51}},
    },
)
def test_post_current_weather_sai_gon(mock_run):
    app = create_app(
        {
            "TESTING": True,
            "WEATHER_API_KEY": "local-key",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "service-role",
            "TELEGRAM_BOT_TOKEN": "bot-token",
            "TELEGRAM_CHAT_ID": "12345",
        }
    )
    client = app.test_client()
    response = client.post(
        "/api/v1/current-weather?location=sai_gon",
        headers={"X-API-Key": "local-key"},
    )
    assert response.status_code == 200
    assert response.get_json()["location_key"] == "sai_gon"
    mock_run.assert_called_once_with(location_key="sai_gon")
