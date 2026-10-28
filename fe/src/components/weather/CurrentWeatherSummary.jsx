import { describeWeather } from "../../lib/weather.js";

export function CurrentWeatherSummary({ data }) {
  const [condition, icon] = describeWeather(data.current.weather_code);
  return (
    <>
      <span class="current-icon" aria-hidden="true">
        {icon}
      </span>
      <div>
        <p class="current-temperature">
          {Math.round(data.current.temperature_2m)}°
        </p>
        <p class="current-condition">{condition}</p>
      </div>
    </>
  );
}
