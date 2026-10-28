"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    WEATHER_API_HOST = os.environ.get("WEATHER_API_HOST", "127.0.0.1")
    WEATHER_API_PORT = int(os.environ.get("WEATHER_API_PORT", "5000"))
    # Comma-separated origins, or "*" for any origin.
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
    # Empty/unset disables auth. When set, /api/v1/* requires X-API-Key or Bearer.
    WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")
    TESTING = False
