"""Shared pytest fixtures for the Flask API."""

import pytest
from app import create_app


@pytest.fixture
def client():
    # Override .env so local secrets do not change default test assumptions.
    app = create_app(
        {
            "TESTING": True,
            "WEATHER_API_KEY": "",
            "SUPABASE_URL": "",
            "SUPABASE_SERVICE_ROLE_KEY": "",
        }
    )
    return app.test_client()
