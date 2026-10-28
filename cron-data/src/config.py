"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    WEATHER_API_HOST = os.environ.get("WEATHER_API_HOST", "127.0.0.1")
    WEATHER_API_PORT = int(os.environ.get("WEATHER_API_PORT", "5000"))
    TESTING = False
