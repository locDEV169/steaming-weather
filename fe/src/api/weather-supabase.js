import {
  isAirQualityPayload,
  isForecastPayload,
  isRainnyPayload,
} from "./weather.js";

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL || "").trim().replace(/\/$/, "");
const supabaseAnonKey = (import.meta.env.VITE_SUPABASE_ANON_KEY || "").trim();
const locationKey = (
  import.meta.env.VITE_SUPABASE_LOCATION_KEY || "da_nang"
).trim() || "da_nang";

/** DB kinds for weather_snapshots (not Flask URL slugs). */
const KIND_WEATHER = "weather";
const KIND_RAINNY = "rainny";
const KIND_AIR_QUALITY = "air_quality";

function requireSupabaseConfig() {
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Thiếu VITE_SUPABASE_URL hoặc VITE_SUPABASE_ANON_KEY trong fe/.env.",
    );
  }
}

/** Shared fetch options for Supabase PostgREST — anon key only. */
export function supabaseFetchInit(init = {}) {
  requireSupabaseConfig();
  const headers = new Headers(init.headers);
  headers.set("apikey", supabaseAnonKey);
  headers.set("Authorization", `Bearer ${supabaseAnonKey}`);
  headers.set("Accept", "application/json");
  return { ...init, headers };
}

function snapshotUrl(kind) {
  requireSupabaseConfig();
  const params = new URLSearchParams({
    select: "location_key,kind,payload,fetched_at",
    location_key: `eq.${locationKey}`,
    kind: `eq.${kind}`,
    limit: "1",
  });
  return `${supabaseUrl}/rest/v1/weather_snapshots?${params}`;
}

async function loadSnapshotPayload(
  kind,
  signal,
  httpErrorMessage,
  validate,
  invalidMessage,
  notFoundMessage,
) {
  const response = await fetch(
    snapshotUrl(kind),
    supabaseFetchInit({ cache: "no-store", signal }),
  );
  if (!response.ok) {
    throw new Error(httpErrorMessage(response.status));
  }

  const rows = await response.json();
  if (!Array.isArray(rows) || rows.length === 0) {
    throw new Error(notFoundMessage);
  }

  const payload = rows[0]?.payload;
  if (!payload || typeof payload !== "object") {
    throw new Error(invalidMessage);
  }
  if (!validate(payload)) {
    throw new Error(invalidMessage);
  }
  return payload;
}

export function fetchForecastFromSupabase(signal) {
  return loadSnapshotPayload(
    KIND_WEATHER,
    signal,
    (status) => `Không tải được snapshot dự báo từ Supabase (HTTP ${status}).`,
    isForecastPayload,
    "Snapshot dự báo thiếu current, hourly hoặc daily.",
    `Chưa có snapshot weather cho location=${locationKey}. Hãy chạy POST /api/v1/ingest.`,
  );
}

export function fetchRainnyFromSupabase(signal) {
  return loadSnapshotPayload(
    KIND_RAINNY,
    signal,
    (status) => `Không tải được snapshot lượng mưa từ Supabase (HTTP ${status}).`,
    isRainnyPayload,
    "Snapshot lượng mưa thiếu days hoặc kind không hợp lệ.",
    `Chưa có snapshot rainny cho location=${locationKey}. Hãy chạy POST /api/v1/ingest.`,
  );
}

export function fetchAirQualityFromSupabase(signal) {
  return loadSnapshotPayload(
    KIND_AIR_QUALITY,
    signal,
    (status) =>
      `Không tải được snapshot chất lượng không khí từ Supabase (HTTP ${status}).`,
    isAirQualityPayload,
    "Snapshot không khí thiếu results.summary hoặc overall.index.",
    `Chưa có snapshot air_quality cho location=${locationKey}. Hãy chạy POST /api/v1/ingest.`,
  );
}
