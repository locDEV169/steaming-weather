import {
  currentDayRainSum,
  describeWeather,
  joinHourlyPrecipProbability,
} from "../../lib/weather.js";

function isUsableNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

function formatMm(value) {
  if (!isUsableNumber(value)) return "—";
  const rounded = Math.round(value * 10) / 10;
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1);
}

function HumidityIcon() {
  return (
    <svg class="now-chip-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M12 3.2c.4.6 6 8.2 6 12.1a6 6 0 1 1-12 0c0-3.9 5.6-11.5 6-12.1z"
      />
    </svg>
  );
}

function WindIcon() {
  return (
    <svg class="now-chip-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        d="M4 8h11a2.5 2.5 0 1 0-2.5-2.5M4 12h15a2.5 2.5 0 1 1-2.5 2.5M4 16h8"
      />
    </svg>
  );
}

export function NowChips({ forecast, airQuality }) {
  const current = forecast?.current ?? {};
  const units = forecast?.current_units ?? {};
  const index = airQuality?.results?.overall?.index;
  const summary = airQuality?.results?.summary;
  const chips = [];

  if (isUsableNumber(current.relative_humidity_2m)) {
    chips.push({
      key: "humidity",
      icon: <HumidityIcon />,
      text: `Ẩm: ${Math.round(current.relative_humidity_2m)}%`,
    });
  }
  if (isUsableNumber(current.wind_speed_10m)) {
    const unit = units.wind_speed_10m || "km/h";
    chips.push({
      key: "wind",
      icon: <WindIcon />,
      text: `Gió: ${Math.round(current.wind_speed_10m)} ${unit}`,
    });
  }
  if (isUsableNumber(index) && summary?.level_vi) {
    chips.push({
      key: "aqi",
      text: `AQI: ${Math.round(index)} • ${summary.level_vi}`,
      className: summary.band_code
        ? `now-chip now-chip--aqi aq-band--${summary.band_code}`
        : "now-chip now-chip--aqi",
    });
  }

  if (chips.length === 0) return null;
  return (
    <div class="now-chips">
      {chips.map((chip) => (
        <span class={chip.className || "now-chip"} key={chip.key}>
          {chip.icon}
          {chip.text}
        </span>
      ))}
    </div>
  );
}

export function CurrentWeatherSummary({ data, rainny, airQuality }) {
  const { current } = data;
  const [condition, icon] = describeWeather(current.weather_code);
  const precipProbability = joinHourlyPrecipProbability(data);
  const rainSum = currentDayRainSum(rainny);
  const feels = isUsableNumber(current.apparent_temperature)
    ? `${Math.round(current.apparent_temperature)}°C`
    : "—";

  const index = airQuality?.results?.overall?.index;
  const summary = airQuality?.results?.summary;

  return (
    <div class="now-card">
      <div class="now-card-main">
        <p class="now-card-title">
          <span aria-hidden="true">{icon}</span> Thời tiết hiện tại
        </p>
        <div class="now-card-main-content">
          <p class="current-temperature">
            {Math.round(current.temperature_2m)}°
          </p>
          <p class="now-feels">Cảm giác như {feels}</p>
          <p class="current-condition">{condition}</p>
        </div>
      </div>
      <div class="now-side">
        <div class="now-mini">
          <p class="now-mini-label">Chỉ số UV</p>
          <div class="now-mini-content">
            <p class="now-mini-value-uv">
              {Math.round(airQuality?.results.uv?.index) || "—"}
            </p>
            <p class="now-mini-note">({airQuality?.results.uv?.level_vi})</p>
          </div>
        </div>
        <div class="now-mini">
          <p class="now-mini-label">Lượng mưa hôm nay</p>
          <p class="now-mini-value-rain">{formatMm(rainSum)} mm</p>
          <p class="now-mini-note">
            Xác suất:{" "}
            {isUsableNumber(precipProbability)
              ? `${Math.round(precipProbability)}%`
              : "—"}
          </p>
        </div>
      </div>
    </div>
  );
}
