import { useEffect, useRef } from "preact/hooks";
import Chart from "chart.js/auto";
import {
  chartOptions,
  createDaylightPlugin,
  makeDatasets,
} from "../../chart/chart-config.js";

export function WeatherChart({ forecast, mode }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const timestamps =
      mode === "daily" ? forecast.daily.time : forecast.hourly.time;
    const codes =
      mode === "daily"
        ? forecast.daily.weather_code
        : forecast.hourly.weather_code;
    const chart = new Chart(canvasRef.current, {
      type: "line",
      data: { labels: timestamps, datasets: makeDatasets(forecast, mode) },
      options: chartOptions(forecast, mode, timestamps, codes),
      plugins: [createDaylightPlugin(forecast, mode, timestamps, codes)],
    });

    return () => chart.destroy();
  }, [forecast, mode]);

  return (
    <div class="chart-wrap">
      <div class="chart-canvas-area">
        <canvas
          ref={canvasRef}
          role="img"
          aria-label="Biểu đồ dự báo thời tiết tại Đà Nẵng"
        />
      </div>
    </div>
  );
}
