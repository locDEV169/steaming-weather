"""Shared HTTP path constants for the weather API (v1)."""

API_V1_PREFIX = "/api/v1"

API_V1_WEATHER = f"{API_V1_PREFIX}/weather"
API_V1_WEATHER_RAINNY_FORECAST = f"{API_V1_PREFIX}/weather-rainny-forecast"
API_V1_AIR_QUALITY = f"{API_V1_PREFIX}/air-quality"
API_V1_SNAPSHOTS = f"{API_V1_PREFIX}/snapshots"
API_V1_SNAPSHOTS_SLUG = f"{API_V1_SNAPSHOTS}/<slug>"
API_V1_INGEST = f"{API_V1_PREFIX}/ingest"
API_V1_INGEST_ALL = f"{API_V1_PREFIX}/ingest-all"
API_V1_CURRENT_WEATHER = f"{API_V1_PREFIX}/current-weather"
API_V1_LIFESTYLE_INSIGHTS = f"{API_V1_PREFIX}/lifestyle-insights"
