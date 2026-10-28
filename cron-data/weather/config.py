"""Open-Meteo request settings and exported column order."""

from pathlib import Path

API_URL = "https://api.open-meteo.com/v1/forecast"
PARAMS = {
    "latitude": 16.0544,
    "longitude": 108.2022,
    "daily": "weather_code,sunrise,rain_sum,sunset,temperature_2m_max,temperature_2m_min",
    "hourly": "temperature_2m,weather_code",
    "current": "weather_code,temperature_2m",
    "timezone": "Asia/Bangkok",
}

CURRENT_COLUMNS = ["time", "interval", "temperature_2m", "weather_code"]
HOURLY_COLUMNS = ["time", "temperature_2m", "weather_code"]
DAILY_COLUMNS = [
    "time",
    "weather_code",
    "sunrise",
    "rain_sum",
    "sunset",
    "temperature_2m_max",
    "temperature_2m_min",
]
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_OUTPUT = OUTPUT_DIR / "open_meteo.json"
CURRENT_OUTPUT = OUTPUT_DIR / "current.csv"
HOURLY_OUTPUT = OUTPUT_DIR / "hourly.csv"
DAILY_OUTPUT = OUTPUT_DIR / "daily.csv"
