"""Unit tests for local Supabase migrate helper."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.migrate import DEFAULT_MIGRATION, resolve_database_url, run_migration


def test_resolve_database_url_requires_value(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "")
    with patch("scripts.migrate.load_dotenv"):
        with pytest.raises(SystemExit, match="DATABASE_URL is empty"):
            resolve_database_url()


def test_resolve_database_url_returns_stripped(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "  postgresql://u:p@host/db  ")
    with patch("scripts.migrate.load_dotenv"):
        assert resolve_database_url() == "postgresql://u:p@host/db"


def test_run_migration_missing_file(tmp_path):
    missing = tmp_path / "nope.sql"
    with pytest.raises(SystemExit, match="not found"):
        run_migration(missing, "postgresql://u:p@host/db")


def test_run_migration_invokes_psql(tmp_path):
    sql = tmp_path / "001.sql"
    sql.write_text("-- noop\n", encoding="utf-8")
    completed = MagicMock(returncode=0)

    with patch("scripts.migrate.subprocess.run", return_value=completed) as run:
        run_migration(sql, "postgresql://user:secret@db.example/postgres")

    run.assert_called_once()
    args = run.call_args.args[0]
    assert args[0] == "psql"
    assert args[1] == "postgresql://user:secret@db.example/postgres"
    assert "-v" in args and "ON_ERROR_STOP=1" in args
    assert str(sql) in args


def test_run_migration_psql_missing_on_path(tmp_path):
    sql = tmp_path / "001.sql"
    sql.write_text("-- noop\n", encoding="utf-8")

    with patch(
        "scripts.migrate.subprocess.run",
        side_effect=FileNotFoundError("psql"),
    ):
        with pytest.raises(SystemExit, match="psql not found") as exc_info:
            run_migration(sql, "postgresql://u:p@host/db")

    message = str(exc_info.value)
    assert "001.sql" in message
    assert "001_weather_snapshots.sql" not in message


def test_default_migration_file_exists():
    assert DEFAULT_MIGRATION.is_file()
    assert DEFAULT_MIGRATION.name == "001_weather_snapshots.sql"
