import { useEffect, useRef } from "preact/hooks";
import Chart from "chart.js/auto";
import {
  makeRainDatasets,
  rainChartOptions,
} from "../../chart/rain-chart-config.js";

export function RainChart({ rainny }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const days = rainny.days;
    const chart = new Chart(canvasRef.current, {
      type: "bar",
      data: {
        labels: days.map((day) => day.date),
        datasets: makeRainDatasets(days),
      },
      options: rainChartOptions(days),
    });

    return () => chart.destroy();
  }, [rainny]);

  return (
    <div class="chart-wrap">
      <div class="chart-canvas-area">
        <canvas
          ref={canvasRef}
          role="img"
          aria-label="Biểu đồ lượng mưa quá khứ và dự báo tại Đà Nẵng"
        />
      </div>
    </div>
  );
}
