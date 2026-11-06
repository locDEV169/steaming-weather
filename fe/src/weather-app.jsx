import { useEffect, useState } from "preact/hooks";
import {
  fetchAirQualityFromSupabase,
  fetchForecastFromSupabase,
  fetchRainnyFromSupabase,
} from "./api/weather-supabase.js";
import { fetchLifestyle } from "./api/weather.js";
import { AirQualitySection } from "./components/weather/AirQualitySection.jsx";
import {
  CurrentWeatherSummary,
  NowChips,
} from "./components/weather/CurrentWeatherSummary.jsx";
import { ForecastSection } from "./components/weather/ForecastSection.jsx";
import { LifestylePage } from "./components/lifestyle/LifestylePage.jsx";
import { PageShell } from "./components/weather/PageShell.jsx";
import { RainForecastSection } from "./components/weather/RainForecastSection.jsx";
import { TopbarMeta } from "./components/weather/TopbarMeta.jsx";
import "./components/lifestyle/lifestyle.css";
import "./components/weather/weather.css";

const SUPABASE_LOAD_HINT =
  " Hãy kiểm tra VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY và đã POST /api/v1/ingest.";

export function App() {
  const [forecast, setForecast] = useState(null);
  const [error, setError] = useState("");
  const [rainny, setRainny] = useState(null);
  const [rainError, setRainError] = useState("");
  const [airQuality, setAirQuality] = useState(null);
  const [aqError, setAqError] = useState("");
  const [lifestyle, setLifestyle] = useState(null);
  const [lifeError, setLifeError] = useState("");
  const [mode, setMode] = useState("overview");
  const [page, setPage] = useState(() =>
    location.hash === "#lifestyle" ? "lifestyle" : "desk",
  );

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

  useEffect(() => {
    const controller = new AbortController();

    fetchLifestyle(controller.signal)
      .then(setLifestyle)
      .catch((loadError) => {
        if (loadError.name !== "AbortError") {
          setLifeError(loadError.message);
        }
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const onHash = () => {
      setPage(location.hash === "#lifestyle" ? "lifestyle" : "desk");
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const loading = !forecast && !error;
  const rainLoading = !rainny && !rainError;
  const aqLoading = !airQuality && !aqError;
  const showOverviewSummary = page === "desk" && mode === "overview";
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
      overviewSummary = (
        <CurrentWeatherSummary
          data={forecast}
          rainny={rainny}
          airQuality={airQuality}
        />
      );
    }
  }

  return (
    <div class="weather-page">
      <header class="topbar">
        <a class="wordmark" href="./" aria-label="Weather desk, trang chủ">
          <span class="wordmark-mark" aria-hidden="true">
            W
          </span>
          <span>
            WEATHER<span class="wordmark-light">DESK</span>
          </span>
        </a>
      </header>
      <main class="weather-page">
        <div class="page-switch" aria-label="Chọn trang">
          <a href="#desk" aria-current={page === "desk" ? "page" : undefined}>
            Biểu đồ
          </a>
          <a
            href="#lifestyle"
            aria-current={page === "lifestyle" ? "page" : undefined}
          >
            Lối sống
          </a>
        </div>
        <PageShell
          updated={
            forecast ? (
              <TopbarMeta data={forecast} />
            ) : loading ? (
              <span class="meta-skeleton" aria-hidden="true" />
            ) : null
          }
          chips={
            forecast ? (
              <NowChips forecast={forecast} airQuality={airQuality} />
            ) : null
          }
          summary={overviewSummary}
        />
        {page === "lifestyle" ? (
          <LifestylePage
            forecast={forecast}
            rainny={rainny}
            airQuality={airQuality}
            lifestyle={lifestyle}
            error={lifeError}
          />
        ) : (
          <>
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
          </>
        )}
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
    </div>
  );
}
