import { useEffect, useState } from "preact/hooks";
import { AirQualitySection } from "./components/weather/AirQualitySection.jsx";
import { CurrentWeatherSummary } from "./components/weather/CurrentWeatherSummary.jsx";
import { ForecastSection } from "./components/weather/ForecastSection.jsx";
import { PageShell } from "./components/weather/PageShell.jsx";
import { RainForecastSection } from "./components/weather/RainForecastSection.jsx";
import { TopbarMeta } from "./components/weather/TopbarMeta.jsx";
import {
  AIR_QUALITY_URL,
  DATA_URL,
  RAINNY_URL,
  isAirQualityPayload,
  isRainnyPayload,
  weatherFetchInit,
} from "./lib/weather.js";

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

    fetch(
      DATA_URL,
      weatherFetchInit({ cache: "no-store", signal: controller.signal }),
    )
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

  useEffect(() => {
    const controller = new AbortController();

    fetch(
      RAINNY_URL,
      weatherFetchInit({ cache: "no-store", signal: controller.signal }),
    )
      .then((response) => {
        if (!response.ok)
          throw new Error(
            `Không tải được dữ liệu lượng mưa (HTTP ${response.status}).`,
          );
        return response.json();
      })
      .then((data) => {
        if (!isRainnyPayload(data)) {
          throw new Error(
            "Phản hồi API lượng mưa thiếu days hoặc kind không hợp lệ.",
          );
        }
        setRainny(data);
      })
      .catch((loadError) => {
        if (loadError.name !== "AbortError") {
          setRainError(
            `${loadError.message} Hãy chạy Flask API (cron-data: python run.py) và Vite (fe: pnpm run dev).`,
          );
        }
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    fetch(
      AIR_QUALITY_URL,
      weatherFetchInit({ cache: "no-store", signal: controller.signal }),
    )
      .then((response) => {
        if (!response.ok)
          throw new Error(
            `Không tải được chất lượng không khí (HTTP ${response.status}).`,
          );
        return response.json();
      })
      .then((data) => {
        if (!isAirQualityPayload(data)) {
          throw new Error(
            "Phản hồi API không khí thiếu results.summary hoặc overall.index.",
          );
        }
        setAirQuality(data);
      })
      .catch((loadError) => {
        if (loadError.name !== "AbortError") {
          setAqError(
            `${loadError.message} Hãy chạy Flask API (cron-data: python run.py) và Vite (fe: pnpm run dev).`,
          );
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
