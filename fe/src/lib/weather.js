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

export const weatherDescriptions = {
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

export function describeWeather(code) {
  return weatherDescriptions[code] ?? ["Chưa xác định", "·"];
}

export function formatWeekday(isoTime) {
  if (typeof isoTime !== "string" || !isoTime.includes("T")) return null;
  const date = new Date(isoTime);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("vi-VN", { weekday: "long" }).format(date);
}

// ponytail: current.time is often :15/:30 while hourly is on the hour — floor then nearest.
export function joinHourlyPrecipProbability(forecast) {
  const currentTime = forecast?.current?.time;
  const times = forecast?.hourly?.time;
  const probs = forecast?.hourly?.precipitation_probability;
  if (
    typeof currentTime !== "string" ||
    !Array.isArray(times) ||
    !Array.isArray(probs) ||
    times.length === 0
  ) {
    return null;
  }

  const [datePart, timePart] = currentTime.split("T");
  const floored =
    datePart && timePart?.length >= 2
      ? `${datePart}T${timePart.slice(0, 2)}:00`
      : null;

  let index = floored ? times.indexOf(floored) : -1;

  if (index < 0) {
    const currentMs = Date.parse(currentTime);
    if (!Number.isFinite(currentMs)) return null;
    let bestDelta = Infinity;
    for (let i = 0; i < times.length; i += 1) {
      const ms = Date.parse(times[i]);
      if (!Number.isFinite(ms)) continue;
      const delta = Math.abs(ms - currentMs);
      if (delta < bestDelta) {
        bestDelta = delta;
        index = i;
      }
    }
  }

  if (index < 0 || index >= probs.length) return null;
  const value = probs[index];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function timestampLabel(value, mode) {
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
