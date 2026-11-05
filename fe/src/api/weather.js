export const DATA_URL = "/api/v1/weather";
export const RAINNY_URL = "/api/v1/weather-rainny-forecast";
export const AIR_QUALITY_URL = "/api/v1/air-quality";

const weatherApiKey = (import.meta.env.VITE_WEATHER_API_KEY || "").trim();

/** Shared fetch options for /api/v1/* — Bearer only when VITE_WEATHER_API_KEY is set. */
export function weatherFetchInit(init = {}) {
  const headers = new Headers(init.headers);
  if (weatherApiKey) {
    headers.set("Authorization", `Bearer ${weatherApiKey}`);
  }
  return { ...init, headers };
}

const AQ_BAND_CODES = new Set([
  "good",
  "fair",
  "moderate",
  "poor",
  "very_poor",
  "extremely_poor",
]);

export function isForecastPayload(data) {
  return Boolean(
    data?.current && data?.hourly?.time?.length && data?.daily?.time?.length,
  );
}

export function isRainnyPayload(data) {
  return (
    Array.isArray(data?.days) &&
    data.days.length > 0 &&
    data.days.every(
      (day) =>
        typeof day?.date === "string" &&
        typeof day?.rain_sum === "number" &&
        (day.kind === "past" ||
          day.kind === "current" ||
          day.kind === "future"),
    )
  );
}

export function isAirQualityPayload(data) {
  const summary = data?.results?.summary;
  const index = data?.results?.overall?.index;
  return (
    summary != null &&
    AQ_BAND_CODES.has(summary.band_code) &&
    typeof summary.level_vi === "string" &&
    summary.level_vi.length > 0 &&
    typeof summary.meaning_vi === "string" &&
    summary.meaning_vi.length > 0 &&
    typeof index === "number" &&
    Number.isFinite(index)
  );
}

async function loadWeatherJson(
  url,
  signal,
  httpErrorMessage,
  validate,
  invalidMessage,
) {
  const response = await fetch(
    url,
    weatherFetchInit({ cache: "no-store", signal }),
  );
  if (!response.ok) {
    throw new Error(httpErrorMessage(response.status));
  }
  const data = await response.json();
  if (!validate(data)) {
    throw new Error(invalidMessage);
  }
  return data;
}

export function fetchForecast(signal) {
  return loadWeatherJson(
    DATA_URL,
    signal,
    (status) => `Không tải được dữ liệu dự báo (HTTP ${status}).`,
    isForecastPayload,
    "Phản hồi API thiếu các phần current, hourly hoặc daily.",
  );
}

export function fetchRainnyForecast(signal) {
  return loadWeatherJson(
    RAINNY_URL,
    signal,
    (status) => `Không tải được dữ liệu lượng mưa (HTTP ${status}).`,
    isRainnyPayload,
    "Phản hồi API lượng mưa thiếu days hoặc kind không hợp lệ.",
  );
}

export function fetchAirQuality(signal) {
  return loadWeatherJson(
    AIR_QUALITY_URL,
    signal,
    (status) => `Không tải được chất lượng không khí (HTTP ${status}).`,
    isAirQualityPayload,
    "Phản hồi API không khí thiếu results.summary hoặc overall.index.",
  );
}
