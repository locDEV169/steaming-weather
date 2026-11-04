"""Apply Supabase SQL migrations from local via psql + DATABASE_URL.

Usage (from cron-data/):
  python scripts/migrate.py
  python scripts/migrate.py path/to/other.sql
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

CRON_DATA_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MIGRATION = (
    CRON_DATA_ROOT / "supabase" / "migrations" / "001_weather_snapshots.sql"
)


def resolve_database_url() -> str:
    load_dotenv(CRON_DATA_ROOT / ".env")
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise SystemExit(
            "DATABASE_URL is empty. Set it in cron-data/.env "
            "(Supabase Dashboard → Project Settings → Database → URI). "
            "Do not use SUPABASE_SERVICE_ROLE_KEY as the DB password."
        )
    return url


def run_migration(sql_path: Path, database_url: str) -> None:
    if not sql_path.is_file():
        raise SystemExit(f"Migration file not found: {sql_path}")

    # Redact password when printing target host for confirmation.
    display = database_url
    if "@" in database_url:
        scheme, _, rest = database_url.partition("://")
        userinfo, _, hostpart = rest.partition("@")
        user = userinfo.split(":", 1)[0]
        display = f"{scheme}://{user}:***@{hostpart}"

    try:
        shown = sql_path.relative_to(CRON_DATA_ROOT)
    except ValueError:
        shown = sql_path
    print(f"Applying {shown} → {display}")


    try:
        completed = subprocess.run(
            [
                "psql",
                database_url,
                "-v",
                "ON_ERROR_STOP=1",
                "-f",
                str(sql_path),
            ],
            check=False,
        )
    except FileNotFoundError as exc:
        raise SystemExit(
            "psql not found on PATH. Install PostgreSQL client tools, "
            "or run the SQL in Supabase SQL Editor "
            f"({DEFAULT_MIGRATION.relative_to(CRON_DATA_ROOT)})."
        ) from exc

    if completed.returncode != 0:
        raise SystemExit(f"psql failed with exit code {completed.returncode}")

    print("Migration applied successfully.")


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]
    sql_path = Path(args[0]) if args else DEFAULT_MIGRATION
    if not sql_path.is_absolute():
        sql_path = (Path.cwd() / sql_path).resolve()
    run_migration(sql_path, resolve_database_url())


if __name__ == "__main__":
    main()
