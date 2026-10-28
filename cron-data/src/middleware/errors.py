"""Global JSON error handlers for uncaught exceptions."""

import logging

from flask import Flask, jsonify  # pyright: ignore[reportMissingImports]
from werkzeug.exceptions import HTTPException  # pyright: ignore[reportMissingImports]

logger = logging.getLogger("weather.api")


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_error):
        return (
            jsonify(
                error={
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found.",
                }
            ),
            404,
        )

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return (
            jsonify(
                error={
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "The HTTP method is not allowed for this resource.",
                }
            ),
            405,
        )

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        # Keep Flask/Werkzeug HTTP errors on their dedicated handlers.
        if isinstance(error, HTTPException):
            return error

        logger.exception("Unhandled exception: %s", error)
        return (
            jsonify(
                error={
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                }
            ),
            500,
        )
