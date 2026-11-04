"""Register cross-cutting HTTP middleware on the Flask app."""

from app.common.auth import register_auth
from app.common.cors import register_cors
from app.common.errors import register_error_handlers
from app.common.request_logging import register_request_logging


def register_middleware(app) -> None:
    register_cors(app)
    register_request_logging(app)
    register_error_handlers(app)
    register_auth(app)
