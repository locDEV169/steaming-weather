import { describeWeather, timestampLabel } from "../lib/weather.js";

export const chartColors = {
  temperature: "#43c6e8",
  rain: "#ff744d",
  max: "#7898ce",
  min: "#e78bd1",
  axis: "#aebbc5",
  grid: "rgba(195, 209, 220, 0.18)",
};

export function makeDatasets(forecast, mode) {
  const { hourly, daily } = forecast;

  if (mode === "daily") {
    return [
      {
        type: "bar",
        label: "Lượng mưa",
        data: daily.rain_sum,
        yAxisID: "rain",
        backgroundColor: "rgba(255, 116, 77, 0.82)",
        borderColor: chartColors.rain,
        borderWidth: 1,
        barPercentage: 0.19,
        categoryPercentage: 0.72,
        order: 4,
      },
      {
        type: "line",
        label: "Nhiệt độ cao nhất",
        data: daily.temperature_2m_max,
        yAxisID: "temperature",
        borderColor: chartColors.max,
        backgroundColor: chartColors.max,
        pointStyle: "triangle",
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 1,
        tension: 0.18,
        order: 2,
      },
      {
        type: "line",
        label: "Nhiệt độ thấp nhất",
        data: daily.temperature_2m_min,
        yAxisID: "temperature",
        borderColor: chartColors.min,
        backgroundColor: chartColors.min,
        pointStyle: "triangle",
        pointRotation: 180,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 1,
        tension: 0.18,
        order: 1,
      },
    ];
  }

  const datasets = [
    {
      type: "line",
      label: "Nhiệt độ",
      data: hourly.temperature_2m,
      yAxisID: "temperature",
      borderColor: chartColors.temperature,
      backgroundColor: "rgba(67, 198, 232, 0.08)",
      borderWidth: 1.6,
      pointRadius: 0,
      pointHitRadius: 8,
      tension: 0.12,
      fill: false,
      order: 1,
    },
  ];

  if (mode === "overview") {
    const dailyValues = (key) => {
      const byDay = new Map(
        daily.time.map((day, index) => [day, daily[key][index]]),
      );
      return hourly.time.map((timestamp) => {
        const [date, time] = timestamp.split("T");
        return time === "12:00" ? (byDay.get(date) ?? null) : null;
      });
    };

    datasets.unshift({
      type: "bar",
      label: "Lượng mưa",
      data: dailyValues("rain_sum"),
      yAxisID: "rain",
      backgroundColor: "rgba(255, 116, 77, 0.88)",
      borderColor: chartColors.rain,
      borderWidth: 1,
      barThickness: 5,
      order: 4,
    });
    datasets.push(
      {
        type: "line",
        label: "Nhiệt độ cao nhất",
        data: dailyValues("temperature_2m_max"),
        yAxisID: "temperature",
        borderColor: chartColors.max,
        backgroundColor: chartColors.max,
        pointStyle: "triangle",
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 1,
        spanGaps: true,
        tension: 0.12,
        order: 2,
      },
      {
        type: "line",
        label: "Nhiệt độ thấp nhất",
        data: dailyValues("temperature_2m_min"),
        yAxisID: "temperature",
        borderColor: chartColors.min,
        backgroundColor: chartColors.min,
        pointStyle: "triangle",
        pointRotation: 180,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 1,
        spanGaps: true,
        tension: 0.12,
        order: 2,
      },
    );
  }

  return datasets;
}

export function createDaylightPlugin(forecast, mode, timestamps, codes) {
  return {
    id: "daylightBands",
    beforeDraw(chart) {
      const { chartArea, scales, ctx } = chart;
      if (!chartArea || mode === "daily") return;

      ctx.save();
      ctx.fillStyle = "rgba(147, 157, 121, 0.105)";
      forecast.daily.time.forEach((date, dayIndex) => {
        const sunrise = forecast.daily.sunrise[dayIndex]
          ?.split("T")[1]
          ?.slice(0, 5);
        const sunset = forecast.daily.sunset[dayIndex]
          ?.split("T")[1]
          ?.slice(0, 5);
        const firstIndex = timestamps.findIndex((value) =>
          value.startsWith(`${date}T`),
        );
        if (firstIndex < 0 || !sunrise || !sunset) return;

        const sunriseHour = Number(sunrise.slice(0, 2));
        const sunsetHour = Number(sunset.slice(0, 2));
        const left = scales.x.getPixelForValue(firstIndex + sunriseHour - 0.5);
        const right = scales.x.getPixelForValue(firstIndex + sunsetHour - 0.5);
        const bandLeft = Math.max(chartArea.left, left);
        const bandRight = Math.min(chartArea.right, right);
        ctx.fillRect(
          bandLeft,
          chartArea.top,
          Math.max(0, bandRight - bandLeft),
          chartArea.bottom - chartArea.top,
        );
      });
      ctx.restore();
    },
    afterDraw(chart) {
      const { chartArea, scales, ctx } = chart;
      if (!chartArea) return;

      const step = mode === "daily" ? 1 : 6;
      ctx.save();
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = "15px 'DM Sans', sans-serif";
      ctx.fillStyle = "#d9e1e6";
      codes.forEach((code, index) => {
        if (index % step !== 0) return;
        const x = scales.x.getPixelForValue(index);
        if (x < chartArea.left + 5 || x > chartArea.right - 5) return;
        ctx.fillText(describeWeather(code)[1], x, chartArea.top + 13);
      });
      ctx.restore();
    },
  };
}

export function chartOptions(forecast, mode, timestamps, codes) {
  const isDaily = mode === "daily";
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    layout: { padding: { top: 24, right: 8, left: 3 } },
    animation: { duration: 420 },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#142231",
        borderColor: "rgba(199, 215, 226, 0.2)",
        borderWidth: 1,
        titleColor: "#f2f5f7",
        bodyColor: "#c5d0d8",
        padding: 11,
        callbacks: {
          title(items) {
            const label = items[0]?.label ?? "";
            if (isDaily) return timestampLabel(label, "daily");
            return new Intl.DateTimeFormat("vi-VN", {
              weekday: "short",
              day: "numeric",
              month: "short",
              hour: "2-digit",
              minute: "2-digit",
            }).format(new Date(label));
          },
          label(context) {
            const unit = context.dataset.yAxisID === "rain" ? " mm" : " °C";
            return ` ${context.dataset.label}: ${context.parsed.y}${unit}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          color(context) {
            return context.index % (isDaily ? 1 : 12) === 0
              ? chartColors.grid
              : "transparent";
          },
          tickLength: 5,
        },
        border: { color: "rgba(197, 211, 222, 0.28)" },
        ticks: {
          color: chartColors.axis,
          autoSkip: false,
          maxRotation: 0,
          padding: 8,
          font: { family: "DM Sans", size: 10 },
          callback(value) {
            return timestampLabel(
              this.getLabelForValue(value),
              isDaily ? "daily" : "hourly",
            );
          },
        },
      },
      temperature: {
        type: "linear",
        position: "left",
        title: { display: true, text: "°C", color: "#aebbc5", align: "end" },
        grid: { color: chartColors.grid, drawTicks: true },
        border: { display: false },
        ticks: {
          color: chartColors.axis,
          padding: 8,
          font: { family: "DM Sans", size: 10 },
        },
        grace: "12%",
      },
      rain: {
        type: "linear",
        position: "right",
        display: mode !== "hourly",
        title: { display: true, text: "mm", color: "#aebbc5", align: "end" },
        grid: { drawOnChartArea: false },
        border: { display: false },
        ticks: {
          color: chartColors.axis,
          padding: 7,
          font: { family: "DM Sans", size: 10 },
        },
        beginAtZero: true,
        suggestedMax: 1,
      },
    },
  };
}
