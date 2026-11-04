import {
  describeWeather,
  formatWeekday,
  joinHourlyPrecipProbability,
} from "../../lib/weather.js";

function isUsableNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

export function CurrentWeatherSummary({ data }) {
  const { current, current_units: units = {}, hourly_units: hourlyUnits = {} } =
    data;
  const [condition, icon] = describeWeather(current.weather_code);
  const weekday = formatWeekday(current.time);
  const precipProbability = joinHourlyPrecipProbability(data);

  const metrics = [];
  if (isUsableNumber(precipProbability)) {
    metrics.push({
      key: "precip",
      label: "Mưa",
      value: `${Math.round(precipProbability)}${hourlyUnits.precipitation_probability || "%"}`,
    });
  }
  if (isUsableNumber(current.relative_humidity_2m)) {
    metrics.push({
      key: "humidity",
      label: "Độ ẩm",
      value: `${Math.round(current.relative_humidity_2m)}${units.relative_humidity_2m || "%"}`,
    });
  }
  if (isUsableNumber(current.apparent_temperature)) {
    metrics.push({
      key: "apparent",
      label: "Cảm giác",
      value: `${Math.round(current.apparent_temperature)}°`,
    });
  }

  return (
    <div class="current-weather current-weather--chart">
      <span class="current-icon" aria-hidden="true">
        {icon}
      </span>
      <div class="current-primary">
        <p class="current-temperature">
          {Math.round(current.temperature_2m)}°
        </p>
        {weekday ? <p class="current-weekday">{weekday}</p> : null}
        <p class="current-condition">{condition}</p>
      </div>
      {metrics.length > 0 ? (
        <p class="current-metrics">
          {metrics.map((metric) => (
            <span class="current-metric" key={metric.key}>
              {metric.label} {metric.value}
            </span>
          ))}
        </p>
      ) : null}
    </div>
  );
}
