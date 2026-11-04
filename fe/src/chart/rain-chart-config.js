import { timestampLabel } from "../lib/weather.js";
import { chartColors } from "./chart-config.js";

export const rainKindColors = {
  past: "rgba(120, 152, 206, 0.85)",
  current: "rgba(255, 116, 77, 0.92)",
  future: "rgba(67, 198, 232, 0.85)",
};

export function makeRainDatasets(days) {
  return [
    {
      type: "bar",
      label: "Lượng mưa",
      data: days.map((day) => day.rain_sum),
      backgroundColor: days.map(
        (day) => rainKindColors[day.kind] ?? rainKindColors.future,
      ),
      borderWidth: 0,
      barPercentage: 0.55,
      categoryPercentage: 0.8,
    },
  ];
}

export function rainChartOptions(days) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title(items) {
            const index = items[0]?.dataIndex;
            return days[index]?.date ?? "";
          },
          afterLabel(item) {
            const kind = days[item.dataIndex]?.kind;
            if (kind === "past") return "Quá khứ";
            if (kind === "current") return "Hiện tại";
            if (kind === "future") return "Dự báo";
            return "";
          },
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: chartColors.axis,
          maxRotation: 0,
          autoSkip: true,
          callback(_value, index) {
            const date = days[index]?.date;
            return date ? timestampLabel(date, "daily") : "";
          },
        },
        grid: { color: chartColors.grid },
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: "mm",
          color: chartColors.axis,
        },
        ticks: { color: chartColors.axis },
        grid: { color: chartColors.grid },
      },
    },
  };
}
