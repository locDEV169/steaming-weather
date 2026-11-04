import { RainChart } from "./RainChart.jsx";
import { RainChartKey } from "./RainChartKey.jsx";

export function RainForecastSection({ rainny, loading, error }) {
  const footnote = rainny
    ? `as_of ${rainny.as_of} · ${rainny.timezone} · Đơn vị ${rainny.unit}`
    : "Lượng mưa theo ngày · Quá khứ · Hiện tại · Dự báo";

  return (
    <section
      class="forecast-section forecast-section--secondary"
      aria-labelledby="rain-chart-title"
    >
      <div class="chart-header">
        <div>
          <p class="eyebrow chart-eyebrow">RAIN OUTLOOK</p>
          <h2 id="rain-chart-title">Lượng mưa quá khứ & dự báo</h2>
        </div>
      </div>

      {!error && <RainChartKey />}
      <div class="chart-frame">
        {loading && (
          <div class="loading-state panel-state" role="status">
            Đang tải biểu đồ lượng mưa...
          </div>
        )}
        {error && (
          <div class="error-state panel-state" role="alert">
            {error}
          </div>
        )}
        {rainny && <RainChart rainny={rainny} />}
      </div>
      <p class="chart-footnote">{footnote}</p>
    </section>
  );
}
