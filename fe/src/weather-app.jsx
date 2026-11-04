import { useEffect, useState } from "preact/hooks";
import { AirQualitySection } from "./components/weather/AirQualitySection.jsx";
import { CurrentWeatherSummary } from "./components/weather/CurrentWeatherSummary.jsx";
import { ForecastSection } from "./components/weather/ForecastSection.jsx";
import { PageShell } from "./components/weather/PageShell.jsx";
import { RainForecastSection } from "./components/weather/RainForecastSection.jsx";
import { TopbarMeta } from "./components/weather/TopbarMeta.jsx";
import {
  fetchAirQualityFromSupabase,
  fetchForecastFromSupabase,
  fetchRainnyFromSupabase,
} from "./api/weather-supabase.js";

const SUPABASE_LOAD_HINT =
  " Hãy kiểm tra VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY và đã POST /api/v1/ingest.";

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

    fetchForecastFromSupabase(controller.signal)
      .then(setForecast)
      .catch((loadError) => {
        if (loadError.name !== "AbortError") {
          setError(`${loadError.message}${SUPABASE_LOAD_HINT}`);
        }
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    fetchRainnyFromSupabase(controller.signal)
      .then(setRainny)
      .catch((loadError) => {
        if (loadError.name !== "AbortError") {
          setRainError(`${loadError.message}${SUPABASE_LOAD_HINT}`);
        }
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    fetchAirQualityFromSupabase(controller.signal)
      .then(setAirQuality)
      .catch((loadError) => {
        if (loadError.name !== "AbortError") {
          setAqError(`${loadError.message}${SUPABASE_LOAD_HINT}`);
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
  console.log("forecast", { forecast });

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
      <AirQualitySection
        airQuality={airQuality}
        loading={aqLoading}
        error={aqError}
      />
      <ForecastSection
        forecast={forecast}
        mode={mode}
        setMode={setMode}
        loading={loading}
        error={error}
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
