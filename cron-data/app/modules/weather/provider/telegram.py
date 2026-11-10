"""Send a plain-text Telegram Bot API message."""

from __future__ import annotations

import requests
from flask import current_app


class TelegramConfigError(RuntimeError):
    """Raised when Telegram bot token or chat id is missing."""


class TelegramSendError(RuntimeError):
    """Raised when Telegram rejects or fails a sendMessage call."""


def _require_telegram_config() -> tuple[str, str]:
    token = (current_app.config.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (current_app.config.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat_id:
        raise TelegramConfigError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be configured."
        )
    return token, chat_id


def send_telegram_message(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Telegram message text must be a non-empty string")
    token, chat_id = _require_telegram_config()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise TelegramSendError("Telegram sendMessage request failed.") from exc
    if response.status_code >= 400:
        raise TelegramSendError(
            f"Telegram sendMessage failed (HTTP {response.status_code})."
        )
    try:
        body = response.json()
    except ValueError as exc:
        raise TelegramSendError("Telegram response is not valid JSON.") from exc
    if not isinstance(body, dict) or body.get("ok") is not True:
        raise TelegramSendError("Telegram sendMessage returned ok=false.")
    return body
