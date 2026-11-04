"""Weather feature module (forecast, rainny, air quality, ingest)."""

from app.modules.weather.routes import weather_blueprint

__all__ = ["weather_blueprint"]
