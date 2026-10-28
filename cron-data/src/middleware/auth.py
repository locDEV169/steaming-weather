"""Optional API-key authentication for /api/v1/* routes."""

from flask import Flask, current_app, jsonify, request  # pyright: ignore[reportMissingImports]

_PROTECTED_PREFIX = "/api/v1/"


def _configured_api_key() -> str:
    return (current_app.config.get("WEATHER_API_KEY") or "").strip()


def _provided_api_key() -> str | None:
    header_key = request.headers.get("X-API-Key")
    if header_key:
        return header_key.strip()

    authorization = request.headers.get("Authorization", "")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() == "bearer" and value.strip():
        return value.strip()
    return None


def register_auth(app: Flask) -> None:
    @app.before_request
    def require_api_key_when_configured():
        expected = _configured_api_key()
        if not expected:
            return None

        if request.method == "OPTIONS":
            return None

        if not request.path.startswith(_PROTECTED_PREFIX):
            return None

        provided = _provided_api_key()
        if provided == expected:
            return None

        return (
            jsonify(
                error={
                    "code": "UNAUTHORIZED",
                    "message": "Missing or invalid API key.",
                }
            ),
            401,
        )
