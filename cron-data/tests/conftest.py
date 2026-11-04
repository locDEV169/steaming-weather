"""Shared pytest fixtures for the Flask API."""

import pytest
from app import create_app


@pytest.fixture
def client():
    # Override .env so local WEATHER_API_KEY does not flip default-auth tests.
    app = create_app({"TESTING": True, "WEATHER_API_KEY": ""})
    return app.test_client()
