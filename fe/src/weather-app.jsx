import { useEffect, useRef, useState } from "preact/hooks";
import Chart from "chart.js/auto";

const DATA_URL = "/api/v1/weather";

const weatherDescriptions = {
  0: ["Nắng quang", "☀"],
  1: ["Ít mây", "◒"],
  2: ["Có mây", "☁"],
  3: ["Nhiều mây", "☁"],
  45: ["Sương mù", "≋"],
  48: ["Sương muối", "≋"],
  51: ["Mưa phùn nhẹ", "☂"],
  53: ["Mưa phùn", "☂"],
  55: ["Mưa phùn dày", "☂"],
  56: ["Mưa phùn đóng băng", "❄"],
  57: ["Mưa phùn đóng băng", "❄"],
  61: ["Mưa nhẹ", "☂"],
  63: ["Mưa vừa", "☂"],
  65: ["Mưa to", "☂"],
  66: ["Mưa đóng băng", "❄"],
  67: ["Mưa đóng băng", "❄"],
  71: ["Tuyết nhẹ", "❄"],
  73: ["Tuyết vừa", "❄"],
  75: ["Tuyết dày", "❄"],
  77: ["Hạt tuyết", "❄"],
  80: ["Mưa rào nhẹ", "☂"],
  81: ["Mưa rào", "☂"],
  82: ["Mưa rào lớn", "☂"],
  85: ["Mưa tuyết nhẹ", "❄"],
  86: ["Mưa tuyết dày", "❄"],
  95: ["Dông", "ϟ"],
  96: ["Dông, mưa đá nhẹ", "ϟ"],
  99: ["Dông, mưa đá", "ϟ"],
};

const chartColors = {
  temperature: "#43c6e8",
  rain: "#ff744d",
  max: "#7898ce",
  min: "#e78bd1",
  axis: "#aebbc5",
  grid: "rgba(195, 209, 220, 0.18)",
};

function describeWeather(code) {
  return weatherDescriptions[code] ?? ["Chưa xác định", "·"];
}

function timestampLabel(value, mode) {
  if (mode === "daily") {
    return new Intl.DateTimeFormat("vi-VN", {
      day: "numeric",
      month: "short",
    }).format(new Date(`${value}T12:00:00`));
  }

  const [date, time] = value.split("T");
  const hour = Number(time.slice(0, 2));
  if (hour === 0) {
    return new Intl.DateTimeFormat("vi-VN", {
      day: "numeric",
      month: "short",
    }).format(new Date(`${date}T12:00:00`));
  }
  return hour === 12 ? "12:00" : "";
}

function makeDatasets(forecast, mode) {
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

function createDaylightPlugin(forecast, mode, timestamps, codes) {
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

function chartOptions(forecast, mode, timestamps, codes) {
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

function WeatherChart({ forecast, mode }) {
  const canvasRef = useRef(null);
  const chartWrapRef = useRef(null);

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

function CurrentWeather({ data }) {
  const [condition, icon] = describeWeather(data.current.weather_code);
  const updatedAt = new Intl.DateTimeFormat("vi-VN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(data.current.time));

  return (
    <>
      <header class="topbar">
        <a class="wordmark" href="./" aria-label="Weather desk, trang chủ">
          <span class="wordmark-mark" aria-hidden="true">
            W
          </span>
          <span>
            WEATHER<span class="wordmark-light">DESK</span>
          </span>
        </a>
        <div class="topbar-meta">
          <span class="live-dot" aria-hidden="true" />
          <span>Cập nhật {updatedAt}</span>
          <span class="meta-divider" aria-hidden="true" />
          <span>{data.timezone_abbreviation || data.timezone}</span>
        </div>
      </header>

      <section class="location-heading" aria-labelledby="page-title">
        <div>
          <p class="eyebrow">OPEN-METEO FORECAST</p>
          <h1 id="page-title">
            Đà Nẵng <span class="heading-coordinate">16.06°N 108.24°E</span>
          </h1>
          <p class="location-subtitle">Dự báo thời tiết · Việt Nam</p>
        </div>
        <div class="current-weather" aria-live="polite">
          <span class="current-icon" aria-hidden="true">
            {icon}
          </span>
          <div>
            <p class="current-temperature">
              {Math.round(data.current.temperature_2m)}°
            </p>
            <p class="current-condition">{condition}</p>
          </div>
        </div>
      </section>
    </>
  );
}

function ChartKey({ mode }) {
  return (
    <div class="chart-key" aria-label="Chú giải biểu đồ">
      {mode !== "daily" && (
        <span class="key-item">
          <i class="key-line key-temperature" aria-hidden="true" />
          Nhiệt độ
        </span>
      )}
      {mode !== "hourly" && (
        <>
          <span class="key-item">
            <i class="key-bar" aria-hidden="true" />
            Lượng mưa
          </span>
          {mode === "overview" && (
            <>
              <span class="key-item">
                <i class="key-point key-max" aria-hidden="true" />
                Cao nhất
              </span>
              <span class="key-item">
                <i class="key-point key-min" aria-hidden="true" />
                Thấp nhất
              </span>
            </>
          )}
        </>
      )}
    </div>
  );
}

function ForecastSection({ forecast, mode, setMode }) {
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
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <ChartKey mode={mode} />
      <div class="chart-frame">
        <WeatherChart forecast={forecast} mode={mode} />
      </div>
      <p class="chart-footnote">{footnote}</p>
    </section>
  );
}

export function App() {
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState("");
  const [mode, setMode] = useState("overview");

  useEffect(() => {
    const controller = new AbortController();

    fetch(DATA_URL, { cache: "no-store", signal: controller.signal })
      .then((response) => {
        if (!response.ok)
          throw new Error(
            `Không tải được dữ liệu dự báo (HTTP ${response.status}).`,
          );
        return response.json();
      })
      .then((data) => {
        if (
          !data.current ||
          !data.hourly?.time?.length ||
          !data.daily?.time?.length
        ) {
          throw new Error(
            "Phản hồi API thiếu các phần current, hourly hoặc daily.",
          );
        }
        setForecast(data);
      })
      .catch((loadError) => {
        if (loadError.name !== "AbortError") {
          setError(
            `${loadError.message} Hãy chạy Flask API (cron-data: python run.py) và Vite (fe: npm run dev).`,
          );
        }
      });

    return () => controller.abort();
  }, []);

  return (
    <main class="weather-page">
      {forecast && <CurrentWeather data={forecast} />}
      {!forecast && !error && (
        <div class="loading-state app-state" role="status">
          Đang tải dữ liệu dự báo...
        </div>
      )}
      {error && (
        <div class="error-state app-state" role="alert">
          {error}
        </div>
      )}
      {forecast && (
        <ForecastSection forecast={forecast} mode={mode} setMode={setMode} />
      )}
      {forecast && (
        <footer class="page-footer">
          <span>
            FORECAST MODEL <strong>Open-Meteo</strong>
          </span>
          <span> Dữ liệu được cập nhật mỗi 6 giờ</span>
          <span>
            latitude: {forecast.latitude.toFixed(4)}
            <br /> longitude: {forecast.longitude.toFixed(4)}
          </span>
        </footer>
      )}
    </main>
  );
}
