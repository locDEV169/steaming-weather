"""CORS headers and preflight handling."""

from flask import Flask, current_app, make_response, request  # pyright: ignore[reportMissingImports]


def _allowed_origin() -> str:
    configured = current_app.config.get("CORS_ORIGINS", "*")
    if configured == "*":
        return "*"

    allowed = [origin.strip() for origin in configured.split(",") if origin.strip()]
    request_origin = request.headers.get("Origin")
    if request_origin and request_origin in allowed:
        return request_origin
    return allowed[0] if allowed else "*"


def register_cors(app: Flask) -> None:
    @app.before_request
    def handle_cors_preflight():
        if request.method != "OPTIONS":
            return None
        response = make_response("", 204)
        response.headers["Access-Control-Allow-Origin"] = _allowed_origin()
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, X-API-Key, Authorization"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        return response

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = _allowed_origin()
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, X-API-Key, Authorization"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        return response
