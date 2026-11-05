"""OpenAPI fragment assemble freshness and conflict checks."""

from __future__ import annotations

import json

from scripts.assemble_openapi import OUTPUT_PATH, assemble


def test_committed_swagger_matches_assemble_from_fragments():
    committed = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    assert committed == assemble()


def test_assemble_includes_weather_paths():
    paths = assemble()["paths"]
    assert "/api/v1/weather" in paths
    assert "/api/v1/weather-rainny-forecast" in paths
    assert "/api/v1/air-quality" in paths
    assert "/api/v1/snapshots/{slug}" in paths
    assert "/api/v1/ingest" in paths
    assert "/api/v1/lifestyle-insights" in paths
