import { useEffect, useState } from "preact/hooks";
import { CurrentWeatherSummary } from "./components/weather/CurrentWeatherSummary.jsx";
import { ForecastSection } from "./components/weather/ForecastSection.jsx";
import { PageShell } from "./components/weather/PageShell.jsx";
import { TopbarMeta } from "./components/weather/TopbarMeta.jsx";
import { DATA_URL } from "./lib/weather.js";

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
            `${loadError.message} Hãy chạy Flask API (cron-data: python run.py) và Vite (fe: pnpm run dev).`,
          );
        }
      });

    return () => controller.abort();
  }, []);

  const loading = !forecast && !error;

  return (
    <main class="weather-page">
      <PageShell
        meta={
          forecast ? (
            <TopbarMeta data={forecast} />
          ) : loading ? (
            <span class="meta-skeleton" aria-hidden="true" />
          ) : null
        }
        current={
          forecast ? (
            <CurrentWeatherSummary data={forecast} />
          ) : loading ? (
            <div class="current-skeleton" aria-hidden="true">
              <span class="skeleton-block skeleton-icon" />
              <div>
                <span class="skeleton-block skeleton-temp" />
                <span class="skeleton-block skeleton-condition" />
              </div>
            </div>
          ) : null
        }
      />
      <ForecastSection
        forecast={forecast}
        mode={mode}
        setMode={setMode}
        loading={loading}
        error={error}
      />
      <footer class="page-footer">
        <span>
          FORECAST MODEL <strong>Open-Meteo</strong>
        </span>
        <span> Dữ liệu được cập nhật mỗi 6 giờ</span>
        {forecast ? (
          <span>
            latitude: {forecast.latitude.toFixed(4)}
            <br /> longitude: {forecast.longitude.toFixed(4)}
          </span>
        ) : (
          <span class="footer-skeleton" aria-hidden="true" />
        )}
      </footer>
    </main>
  );
}
