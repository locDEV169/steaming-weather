"""HTTP route registrations for the weather module."""

from app.modules.weather.routes.weather_routes import weather_blueprint

__all__ = ["weather_blueprint"]
