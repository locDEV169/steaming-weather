"""Upsert shaped weather snapshots into Supabase PostgREST."""

from __future__ import annotations

from datetime import datetime, timezone

import requests
from flask import current_app

SNAPSHOT_KINDS = ("weather", "rainny", "air_quality")


class SupabaseConfigError(RuntimeError):
    """Raised when Supabase URL or service role key is missing."""


class SupabaseWriteError(RuntimeError):
    """Raised when PostgREST rejects or fails an upsert."""


class SupabaseReadError(RuntimeError):
    """Raised when PostgREST rejects or fails a snapshot read."""


class SnapshotNotFoundError(LookupError):
    """Raised when no snapshot row exists for location_key + kind."""


class LifestyleNotFoundError(LookupError):
    """Raised when no lifestyle_insights row exists for the location."""


class CurrentWeatherNotFoundError(LookupError):
    """Raised when no current_weather row exists for the location."""


def _require_supabase_config() -> tuple[str, str, str]:
    url = (current_app.config.get("SUPABASE_URL") or "").strip().rstrip("/")
    key = (current_app.config.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    location = (current_app.config.get("SUPABASE_LOCATION_KEY") or "da_nang").strip()
    if not url or not key:
        raise SupabaseConfigError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
        )
    if not location:
        location = "da_nang"
    return url, key, location


def upsert_snapshot(
    kind: str, payload: dict, fetched_at: datetime | None = None
) -> dict:
    """Upsert one latest-only snapshot row. Returns the written row metadata."""
    if kind not in SNAPSHOT_KINDS:
        raise ValueError(f"Unsupported snapshot kind: {kind}")
    if not isinstance(payload, dict):
        raise TypeError("payload must be a JSON object")

    base_url, service_key, location_key = _require_supabase_config()
    when = fetched_at or datetime.now(timezone.utc)  # noqa: UP017
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)  # noqa: UP017
    fetched_at_iso = when.isoformat()

    body = {
        "location_key": location_key,
        "kind": kind,
        "payload": payload,
        "fetched_at": fetched_at_iso,
        "updated_at": fetched_at_iso,
    }
    try:
        response = requests.post(
            f"{base_url}/rest/v1/weather_snapshots",
            params={"on_conflict": "location_key,kind"},
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=representation",
            },
            json=body,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise SupabaseWriteError(f"Supabase upsert request failed for {kind}.") from exc
    if response.status_code >= 400:
        raise SupabaseWriteError(
            f"Supabase upsert failed for {kind} (HTTP {response.status_code})."
        )

    rows = response.json()
    row = rows[0] if isinstance(rows, list) and rows else body
    return {
        "location_key": row.get("location_key", location_key),
        "kind": row.get("kind", kind),
        "fetched_at": row.get("fetched_at", fetched_at_iso),
    }


def insert_lifestyle_insight(
    payload: dict, fetched_at: datetime | None = None
) -> dict:
    """Append one lifestyle forecast row. Never updates an existing row."""
    if not isinstance(payload, dict):
        raise TypeError("payload must be a JSON object")

    base_url, service_key, location_key = _require_supabase_config()
    when = fetched_at or datetime.now(timezone.utc)  # noqa: UP017
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)  # noqa: UP017
    fetched_at_iso = when.isoformat()
    body = {
        "location_key": location_key,
        "payload": payload,
        "fetched_at": fetched_at_iso,
    }
    try:
        response = requests.post(
            f"{base_url}/rest/v1/lifestyle_insights",
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            json=body,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise SupabaseWriteError("Supabase insert request failed for lifestyle.") from exc
    if response.status_code >= 400:
        raise SupabaseWriteError(
            f"Supabase insert failed for lifestyle (HTTP {response.status_code})."
        )

    rows = response.json()
    row = rows[0] if isinstance(rows, list) and rows else body
    return {
        "id": row.get("id"),
        "location_key": row.get("location_key", location_key),
        "fetched_at": row.get("fetched_at", fetched_at_iso),
    }


def get_latest_lifestyle_insight() -> dict:
    """Return the lifestyle row with the greatest fetched_at for this location."""
    base_url, service_key, location_key = _require_supabase_config()
    try:
        response = requests.get(
            f"{base_url}/rest/v1/lifestyle_insights",
            params={
                "select": "id,location_key,payload,fetched_at",
                "location_key": f"eq.{location_key}",
                "order": "fetched_at.desc",
                "limit": "1",
            },
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Accept": "application/json",
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        raise SupabaseReadError("Supabase lifestyle read failed.") from exc
    if response.status_code >= 400:
        raise SupabaseReadError(
            f"Supabase lifestyle read failed (HTTP {response.status_code})."
        )
    try:
        rows = response.json()
    except ValueError as exc:
        raise SupabaseReadError("Supabase lifestyle response is not valid JSON.") from exc
    if not isinstance(rows, list) or not rows:
        raise LifestyleNotFoundError(
            f"No lifestyle insight found for location={location_key!r}."
        )
    row = rows[0]
    if not isinstance(row, dict) or not isinstance(row.get("payload"), dict):
        raise SupabaseReadError("Supabase lifestyle row is invalid.")
    return row


def get_current_weather() -> dict:
    """Return the current_weather row with the greatest fetched_at for this location."""
    base_url, service_key, location_key = _require_supabase_config()
    try:
        response = requests.get(
            f"{base_url}/rest/v1/current_weather",
            params={
                "select": "id,location_key,payload,fetched_at",
                "location_key": f"eq.{location_key}",
                "order": "fetched_at.desc",
                "limit": "1",
            },
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Accept": "application/json",
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        raise SupabaseReadError(
            "Supabase current_weather read failed."
        ) from exc
    if response.status_code >= 400:
        raise SupabaseReadError(
            f"Supabase current_weather read failed (HTTP {response.status_code})."
        )
    try:
        rows = response.json()
    except ValueError as exc:
        raise SupabaseReadError(
            "Supabase current_weather response is not valid JSON."
        ) from exc
    if not isinstance(rows, list) or not rows:
        raise CurrentWeatherNotFoundError(
            f"No current weather found for location={location_key!r}."
        )
    row = rows[0]
    if not isinstance(row, dict) or not isinstance(row.get("payload"), dict):
        raise SupabaseReadError("Supabase current_weather row is invalid.")
    return {
        "id": row.get("id"),
        "location_key": row.get("location_key", location_key),
        "fetched_at": row.get("fetched_at"),
        "payload": row["payload"],
    }


def insert_current_weather(
    payload: dict, fetched_at: datetime | None = None
) -> dict:
    """Append one current_weather row. Never updates an existing row."""
    if not isinstance(payload, dict):
        raise TypeError("payload must be a JSON object")

    base_url, service_key, location_key = _require_supabase_config()
    when = fetched_at or datetime.now(timezone.utc)  # noqa: UP017
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)  # noqa: UP017
    fetched_at_iso = when.isoformat()
    body = {
        "location_key": location_key,
        "payload": payload,
        "fetched_at": fetched_at_iso,
    }
    try:
        response = requests.post(
            f"{base_url}/rest/v1/current_weather",
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            json=body,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise SupabaseWriteError(
            "Supabase insert request failed for current_weather."
        ) from exc
    if response.status_code >= 400:
        raise SupabaseWriteError(
            f"Supabase insert failed for current_weather "
            f"(HTTP {response.status_code})."
        )

    rows = response.json()
    row = rows[0] if isinstance(rows, list) and rows else body
    return {
        "id": row.get("id"),
        "location_key": row.get("location_key", location_key),
        "fetched_at": row.get("fetched_at", fetched_at_iso),
    }


def get_snapshot(kind: str) -> dict:
    """Fetch one latest snapshot payload for the configured location."""
    if kind not in SNAPSHOT_KINDS:
        raise ValueError(f"Unsupported snapshot kind: {kind}")

    base_url, service_key, location_key = _require_supabase_config()
    try:
        response = requests.get(
            f"{base_url}/rest/v1/weather_snapshots",
            params={
                "select": "location_key,kind,payload,fetched_at",
                "location_key": f"eq.{location_key}",
                "kind": f"eq.{kind}",
                "limit": "1",
            },
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}",
                "Accept": "application/json",
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        raise SupabaseReadError(
            f"Supabase snapshot request failed for {kind}."
        ) from exc
    if response.status_code >= 400:
        raise SupabaseReadError(
            f"Supabase snapshot read failed for {kind} (HTTP {response.status_code})."
        )

    try:
        rows = response.json()
    except ValueError as exc:
        raise SupabaseReadError(
            f"Supabase snapshot response is not valid JSON for {kind}."
        ) from exc
    if not isinstance(rows, list) or not rows:
        raise SnapshotNotFoundError(
            f"No snapshot found for location={location_key!r} kind={kind!r}."
        )

    row = rows[0]
    if not isinstance(row, dict):
        raise SupabaseReadError(f"Supabase snapshot row is invalid for {kind}.")
    payload = row.get("payload")
    if not isinstance(payload, dict):
        raise SupabaseReadError(f"Supabase snapshot payload is invalid for {kind}.")
    return payload
