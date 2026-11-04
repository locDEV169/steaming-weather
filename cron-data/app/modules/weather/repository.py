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


def upsert_snapshot(kind: str, payload: dict, fetched_at: datetime | None = None) -> dict:
    """Upsert one latest-only snapshot row. Returns the written row metadata."""
    if kind not in SNAPSHOT_KINDS:
        raise ValueError(f"Unsupported snapshot kind: {kind}")
    if not isinstance(payload, dict):
        raise TypeError("payload must be a JSON object")

    base_url, service_key, location_key = _require_supabase_config()
    when = fetched_at or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
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
        raise SupabaseWriteError(
            f"Supabase upsert request failed for {kind}."
        ) from exc
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
