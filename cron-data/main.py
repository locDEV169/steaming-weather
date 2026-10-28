"""Fetch Open-Meteo current, hourly, and daily forecast data."""

from weather.api import fetch_forecast
from weather.config import CURRENT_OUTPUT, DAILY_OUTPUT, HOURLY_OUTPUT, RAW_OUTPUT
from weather.storage import save_forecast


def main() -> None:
    try:
        payload = fetch_forecast()
        row_counts = save_forecast(payload)
    except Exception as error:
        raise SystemExit(f"Không thể lấy hoặc lưu dữ liệu thời tiết: {error}") from error

    print(f"Đã lưu JSON thô: {RAW_OUTPUT}")
    print(f"Đã lưu CSV hiện tại: {CURRENT_OUTPUT} ({row_counts[CURRENT_OUTPUT.name]} dòng)")
    print(f"Đã lưu CSV theo giờ: {HOURLY_OUTPUT} ({row_counts[HOURLY_OUTPUT.name]} dòng)")
    print(f"Đã lưu CSV theo ngày: {DAILY_OUTPUT} ({row_counts[DAILY_OUTPUT.name]} dòng)")


if __name__ == "__main__":
    main()