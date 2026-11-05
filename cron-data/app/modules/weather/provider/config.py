"""Open-Meteo request settings and exported column order."""

from pathlib import Path

API_URL = "https://api.open-meteo.com/v1/forecast"
PARAMS = {
    "latitude": 16.0544,
    "longitude": 108.2022,
    "daily": (
        "weather_code,sunrise,rain_sum,precipitation_sum,precipitation_probability_max,"
        "sunset,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,wind_gusts_10m_max"
    ),
    "hourly": (
        "temperature_2m,weather_code,precipitation_probability,precipitation,rain,showers,"
        "wind_speed_10m,wind_gusts_10m,apparent_temperature"
    ),
    "current": (
        "weather_code,temperature_2m,relative_humidity_2m,is_day,apparent_temperature,"
        "precipitation,rain,showers,wind_speed_10m,wind_gusts_10m"
    ),
    "timezone": "Asia/Bangkok",
    "forecast_days": 7,
    "past_days": 7,
}

CURRENT_COLUMNS = [
    "time",
    "interval",
    "temperature_2m",
    "weather_code",
    "relative_humidity_2m",
    "is_day",
    "apparent_temperature",
    "precipitation",
    "rain",
    "showers",
    "wind_speed_10m",
    "wind_gusts_10m",
]

HOURLY_COLUMNS = [
    "time",
    "temperature_2m",
    "weather_code",
    "precipitation_probability",
    "precipitation",
    "rain",
    "showers",
    "wind_speed_10m",
    "wind_gusts_10m",
]

DAILY_COLUMNS = [
    "time",
    "weather_code",
    "sunrise",
    "rain_sum",
    "sunset",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
]
# cron-data/data — this file lives at app/modules/weather/provider/
OUTPUT_DIR = Path(__file__).resolve().parents[4] / "data"
RAW_OUTPUT = OUTPUT_DIR / "open_meteo.json"
CURRENT_OUTPUT = OUTPUT_DIR / "current.csv"
HOURLY_OUTPUT = OUTPUT_DIR / "hourly.csv"
DAILY_OUTPUT = OUTPUT_DIR / "daily.csv"
