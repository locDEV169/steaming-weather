"""Convert Open-Meteo response sections into tabular data."""

import pandas as pd

from weather.config import CURRENT_COLUMNS, DAILY_COLUMNS, HOURLY_COLUMNS

SECTION_COLUMNS = {
    "current": CURRENT_COLUMNS,
    "hourly": HOURLY_COLUMNS,
    "daily": DAILY_COLUMNS,
}


def to_frame(section: str, values: dict) -> pd.DataFrame:
    if section not in SECTION_COLUMNS:
        raise ValueError(f"Unsupported forecast section: {section}")
    if not isinstance(values, dict):
        raise ValueError(f"Response section '{section}' must be an object")  # noqa: TRY004

    columns = SECTION_COLUMNS[section]
    missing = [column for column in columns if column not in values]
    if missing:
        raise ValueError(f"Missing columns in '{section}': {', '.join(missing)}")

    if section == "current":
        return pd.DataFrame([{column: values[column] for column in columns}])

    try:
        frame = pd.DataFrame(values)
    except ValueError as error:
        raise ValueError(f"Invalid columns in '{section}': {error}") from error
    return frame[columns]