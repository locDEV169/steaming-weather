"""Weather data-access repositories."""

from app.modules.weather.repositories.snapshots import (
    SNAPSHOT_KINDS,
    LifestyleNotFoundError,
    SnapshotNotFoundError,
    SupabaseConfigError,
    SupabaseReadError,
    SupabaseWriteError,
    get_latest_lifestyle_insight,
    get_snapshot,
    insert_lifestyle_insight,
    upsert_snapshot,
)

__all__ = [
    "SNAPSHOT_KINDS",
    "LifestyleNotFoundError",
    "SnapshotNotFoundError",
    "SupabaseConfigError",
    "SupabaseReadError",
    "SupabaseWriteError",
    "get_latest_lifestyle_insight",
    "get_snapshot",
    "insert_lifestyle_insight",
    "upsert_snapshot",
]
