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
