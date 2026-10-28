"""Shared pytest fixtures for the Flask API."""

import pytest
from src import create_app


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    return app.test_client()