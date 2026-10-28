"""Local development entry point for the Flask weather API."""

from src import create_app

app = create_app()


if __name__ == "__main__":
    app.run(
        host=app.config["WEATHER_API_HOST"],
        port=app.config["WEATHER_API_PORT"],
    )