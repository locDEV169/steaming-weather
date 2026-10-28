"""Register cross-cutting HTTP middleware on the Flask app."""

from src.middleware.auth import register_auth
from src.middleware.cors import register_cors
from src.middleware.errors import register_error_handlers
from src.middleware.request_logging import register_request_logging


def register_middleware(app) -> None:
    register_cors(app)
    register_request_logging(app)
    register_error_handlers(app)
    register_auth(app)
