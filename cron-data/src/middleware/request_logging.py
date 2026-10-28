"""Log method, path, status, and duration for each request."""

import logging
import time

from flask import Flask, g, request  # pyright: ignore[reportMissingImports]

logger = logging.getLogger("weather.api")


def register_request_logging(app: Flask) -> None:
    @app.before_request
    def start_timer():
        g.request_started_at = time.perf_counter()

    @app.after_request
    def log_request(response):
        started_at = getattr(g, "request_started_at", None)
        duration_ms = (
            round((time.perf_counter() - started_at) * 1000, 1)
            if started_at is not None
            else None
        )
        logger.info(
            "%s %s -> %s (%sms)",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response
