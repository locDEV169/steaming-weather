"""Assemble modular OpenAPI fragments into app/static/swagger.json.

Usage (from cron-data/):
  python scripts/assemble_openapi.py

Sources:
  app/openapi/root.json
  app/openapi/components.json
  app/modules/*/openapi/paths.json
  app/modules/*/openapi/schemas.json (optional)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

CRON_DATA_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = CRON_DATA_ROOT / "app"
OPENAPI_ROOT = APP_ROOT / "openapi"
MODULES_ROOT = APP_ROOT / "modules"
OUTPUT_PATH = APP_ROOT / "static" / "swagger.json"


def load_json(path: Path) -> Any:
    if not path.is_file():
        raise SystemExit(f"OpenAPI fragment not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def merge_dict(target: dict[str, Any], incoming: dict[str, Any], *, label: str) -> None:
    for key, value in incoming.items():
        if key in target and target[key] != value:
            raise SystemExit(
                f"OpenAPI assemble conflict in {label}: duplicate key {key!r}"
            )
        target[key] = value


def assemble() -> dict[str, Any]:
    root = load_json(OPENAPI_ROOT / "root.json")
    shared = load_json(OPENAPI_ROOT / "components.json")

    doc: dict[str, Any] = {
        "openapi": root["openapi"],
        "info": root["info"],
        "servers": root["servers"],
        "paths": {},
        "components": {
            "securitySchemes": dict(shared.get("securitySchemes") or {}),
            "schemas": dict((shared.get("schemas") or {})),
        },
    }

    path_files = sorted(MODULES_ROOT.glob("*/openapi/paths.json"))
    if not path_files:
        raise SystemExit(f"No module OpenAPI paths found under {MODULES_ROOT}")

    for paths_path in path_files:
        module_name = paths_path.parent.parent.name
        merge_dict(doc["paths"], load_json(paths_path), label=f"paths/{module_name}")

        schemas_path = paths_path.parent / "schemas.json"
        if schemas_path.is_file():
            merge_dict(
                doc["components"]["schemas"],
                load_json(schemas_path),
                label=f"schemas/{module_name}",
            )

    return doc


def write_swagger(doc: dict[str, Any], path: Path = OUTPUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    doc = assemble()
    write_swagger(doc)
    print(f"Wrote {OUTPUT_PATH.relative_to(CRON_DATA_ROOT)} ({len(doc['paths'])} paths)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
