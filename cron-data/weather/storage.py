"""Write the raw response and tabular forecast sections to disk."""

import json
from pathlib import Path

from weather.config import (
    CURRENT_OUTPUT,
    DAILY_OUTPUT,
    HOURLY_OUTPUT,
    OUTPUT_DIR,
    RAW_OUTPUT,
)
from weather.transform import to_frame


def save_forecast(payload: dict) -> dict[str, int]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    outputs = {
        "current": CURRENT_OUTPUT,
        "hourly": HOURLY_OUTPUT,
        "daily": DAILY_OUTPUT,
    }
    row_counts = {}
    for section, output_path in outputs.items():
        frame = to_frame(section, payload[section])
        frame.to_csv(output_path, index=False, encoding="utf-8-sig")
        row_counts[Path(output_path).name] = len(frame)

    return row_counts