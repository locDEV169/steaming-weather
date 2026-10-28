"""Flask application factory for the weather API."""

from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

from src.config import Config


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    SWAGGER_URL = "/api/docs"  # URL for exposing Swagger UI
    API_URL = "/static/swagger.json"  # Path to your local static file
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={"app_name": "My Flask API Documentation"}
    )
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    from src.routes.weather_routes import weather_blueprint

    app.register_blueprint(weather_blueprint)
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    return app
