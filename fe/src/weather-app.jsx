import { useEffect, useState } from "preact/hooks";
import {
  fetchAirQuality,
  fetchForecast,
  fetchRainnyForecast,
} from "./api/weather.js";
import { AirQualitySection } from "./components/weather/AirQualitySection.jsx";
import { CurrentWeatherSummary } from "./components/weather/CurrentWeatherSummary.jsx";
import { ForecastSection } from "./components/weather/ForecastSection.jsx";
import { PageShell } from "./components/weather/PageShell.jsx";
import { RainForecastSection } from "./components/weather/RainForecastSection.jsx";
import { TopbarMeta } from "./components/weather/TopbarMeta.jsx";

const API_LOAD_HINT =
  " Hãy chạy Flask API (cron-data: python run.py) và Vite (fe: pnpm run dev). Kiểm tra VITE_WEATHER_API_KEY khớp WEATHER_API_KEY.";

export function App() {
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState("");
  const [rainny, setRainny] = useState(null);
  const [rainError, setRainError] = useState("");
  const [airQuality, setAirQuality] = useState(null);
  const [aqError, setAqError] = useState("");
  const [mode, setMode] = useState("overview");

  useEffect(() => {
    const controller = new AbortController();

    fetchForecast(controller.signal)
      .then(setForecast)
      .catch((loadError) => {
        if (loadError.name !== "AbortError") {
          setError(`${loadError.message}${API_LOAD_HINT}`);
        }
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    fetchRainnyForecast(controller.signal)
      .then(setRainny)
      .catch((loadError) => {
        if (loadError.name !== "AbortError") {
          setRainError(`${loadError.message}${API_LOAD_HINT}`);
        }
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    fetchAirQuality(controller.signal)
      .then(setAirQuality)
      .catch((loadError) => {
        if (loadError.name !== "AbortError") {
          setAqError(`${loadError.message}${API_LOAD_HINT}`);
        }
      });

    return () => controller.abort();
  }, []);

  const loading = !forecast && !error;
  const rainLoading = !rainny && !rainError;
  const aqLoading = !airQuality && !aqError;
  const showOverviewSummary = mode === "overview";
  let overviewSummary = null;
  if (showOverviewSummary) {
    if (loading) {
      overviewSummary = (
        <div class="current-skeleton" aria-hidden="true">
          <span class="skeleton-block skeleton-icon" />
          <div>
            <span class="skeleton-block skeleton-temp" />
            <span class="skeleton-block skeleton-condition" />
            <span class="skeleton-block skeleton-metrics" />
          </div>
        </div>
      );
    } else if (forecast && !error) {
      overviewSummary = <CurrentWeatherSummary data={forecast} />;
    }
  }

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
        summary={overviewSummary}
      />
      <ForecastSection
        forecast={forecast}
        mode={mode}
        setMode={setMode}
        loading={loading}
        error={error}
      />
      <AirQualitySection
        airQuality={airQuality}
        loading={aqLoading}
        error={aqError}
      />
      <RainForecastSection
        rainny={rainny}
        loading={rainLoading}
        error={rainError}
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
