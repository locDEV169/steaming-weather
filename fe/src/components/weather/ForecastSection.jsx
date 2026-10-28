import { ChartKey } from "./ChartKey.jsx";
import { WeatherChart } from "./WeatherChart.jsx";

export function ForecastSection({ forecast, mode, setMode, loading, error }) {
  const modes = [
    ["overview", "Tổng quan"],
    ["hourly", "Theo giờ"],
    ["daily", "Theo ngày"],
  ];
  const footnote =
    mode === "daily"
      ? "Dữ liệu theo ngày · Nhiệt độ °C · Lượng mưa mm"
      : mode === "hourly"
        ? "Dữ liệu theo giờ · Nhiệt độ °C"
        : "Dữ liệu theo giờ · Nhiệt độ °C · Lượng mưa mm · Vùng sáng thể hiện ban ngày";

  return (
    <section class="forecast-section" aria-labelledby="chart-title">
      <div class="chart-header">
        <div>
          <p class="eyebrow chart-eyebrow">WEATHER OUTLOOK</p>
          <h2 id="chart-title">Diễn biến dự báo</h2>
        </div>
        <div
          class="view-switch"
          role="group"
          aria-label="Chọn khoảng thời gian biểu đồ"
        >
          {modes.map(([value, label]) => (
            <button
              type="button"
              class={`view-button${mode === value ? " is-active" : ""}`}
              aria-pressed={mode === value}
              onClick={() => setMode(value)}
              disabled={Boolean(loading || error)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {!error && <ChartKey mode={mode} />}
      <div class="chart-frame">
        {loading && (
          <div class="loading-state panel-state" role="status">
            Đang tải biểu đồ dự báo...
          </div>
        )}
        {error && (
          <div class="error-state panel-state" role="alert">
            {error}
          </div>
        )}
        {forecast && <WeatherChart forecast={forecast} mode={mode} />}
      </div>
      <p class="chart-footnote">{footnote}</p>
    </section>
  );
}
