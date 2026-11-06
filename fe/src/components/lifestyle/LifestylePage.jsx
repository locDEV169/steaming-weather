import { useState } from "preact/hooks";
import { describeWeather } from "../../lib/weather.js";
import { CurrentWeatherSummary } from "../weather/CurrentWeatherSummary.jsx";

function scoreWidth(score) {
  if (typeof score !== "number" || !Number.isFinite(score)) return 0;
  return Math.min(100, Math.max(0, score));
}

function lowestWeatherHour(hours) {
  if (!Array.isArray(hours)) return null;
  let chosen = null;
  for (const hour of hours) {
    const code = hour?.weather_code;
    if (typeof code !== "number" || !Number.isFinite(code)) continue;
    if (chosen === null || code < chosen.weather_code) chosen = hour;
  }

  return chosen;
}

function dayLabel(date, today) {
  const [year, month, day] = date.split("-");
  const stamp = `${day}/${month}`;
  if (date === today) return `Hôm nay (${stamp})`;
  const parsed = new Date(`${date}T12:00:00`);
  const weekday = new Intl.DateTimeFormat("vi-VN", { weekday: "long" }).format(
    parsed,
  );
  return `${weekday} (${stamp})`;
}

function forecastDays(forecast) {
  const daily = forecast?.daily;
  if (!daily?.time?.length) return [];
  const today = forecast.current?.time?.slice(0, 10);
  const startAt = today ? daily.time.indexOf(today) : 0;
  const start = startAt < 0 ? 0 : startAt;
  return daily.time.slice(start, start + 3).map((date, offset) => {
    const index = start + offset;
    return {
      id: date,
      label: dayLabel(date, today),
      tempMin: daily.temperature_2m_min?.[index],
      tempMax: daily.temperature_2m_max?.[index],
      rainSum: daily.rain_sum?.[index],
      condition: describeWeather(daily.weather_code?.[index])[0],
    };
  });
}

function roundOrDash(value) {
  return typeof value === "number" && Number.isFinite(value)
    ? String(Math.round(value))
    : "—";
}

function convertUTCStamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const hh = String(date.getUTCHours()).padStart(2, "0");
  const mm = String(date.getUTCMinutes()).padStart(2, "0");
  const dd = String(date.getUTCDate()).padStart(2, "0");
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  return `${hh}:${mm}, ${dd}/${month}/${date.getUTCFullYear()}`;
}

export function LifestylePage({
  forecast,
  rainny,
  airQuality,
  lifestyle,
  error,
}) {
  const days = forecastDays(forecast);
  const [selected, setSelected] = useState(0);
  const day = days[selected] ?? null;
  const laundry = lifestyle?.laundry;
  const dryingHour = lowestWeatherHour(laundry?.hours);
  const carWash = lifestyle?.car_wash;
  const upcoming = Array.isArray(rainny?.days)
    ? rainny.days.filter((item) => item.kind === "future").slice(0, 3)
    : [];

  return (
    <div class="life-page">
      <section class="life-hero">
        {forecast ? (
          <CurrentWeatherSummary
            data={forecast}
            rainny={rainny}
            airQuality={airQuality}
          />
        ) : (
          <p class="life-empty">Chưa có thời tiết hiện tại.</p>
        )}
        <aside class="life-note">
          <p class="life-kicker">Trợ lý thông tin</p>
          <h2>Khuyến cáo đang có</h2>
          <p>
            {lifestyle?.as_of ? `mốc ${convertUTCStamp(lifestyle.as_of)}` : ""}.
          </p>
        </aside>
      </section>

      <section class="life-section" aria-labelledby="lifestyle-title">
        <div class="life-section-head">
          <div>
            <h2 id="lifestyle-title">
              <span class="life-title-mark" aria-hidden="true">
                ✦
              </span>
              Dự báo theo ngữ cảnh hành vi & lối sống
            </h2>
            <span>
              Điểm số lấy từ bản đánh giá mới nhất, không đổi theo ngày đang
              chọn.
            </span>
          </div>
          {days.length > 0 && (
            <div class="life-tabs" role="tablist" aria-label="Chọn ngày dự báo">
              {days.map((item, index) => (
                <button
                  key={item.id}
                  type="button"
                  role="tab"
                  aria-selected={index === selected}
                  class={index === selected ? "is-active" : ""}
                  onClick={() => setSelected(index)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {day && (
          <p class="life-dayline">
            {day.condition} · {roundOrDash(day.tempMin)}°C –{" "}
            {roundOrDash(day.tempMax)}°C · mưa{" "}
            {typeof day.rainSum === "number" ? day.rainSum : "—"} mm
          </p>
        )}
        {error && <p class="life-error">{error}</p>}

        <div class="life-grid">
          <article class="life-card">
            <header class="life-card-top">
              <div class="life-card-id">
                <span class="life-icon life-icon--sun" aria-hidden="true">
                  ○
                </span>
                <div>
                  <h3>Chỉ số phơi đồ</h3>
                  <p>Điểm khô của 3 giờ gần nhất</p>
                </div>
              </div>
              <span class="life-badge">
                {laundry?.status ?? "—"}
                {typeof laundry?.score === "number"
                  ? ` · ${Math.round(laundry.score)}/100`
                  : ""}
              </span>
            </header>
            <div class="life-metrics">
              <div>
                <p>Khung giờ phơi tối ưu</p>
                <strong>{convertUTCStamp(dryingHour?.time)}</strong>
              </div>
              <div>
                <p>Thời gian khô ước tính</p>
                <strong>{laundry?.dry_time ?? "—"}</strong>
                <strong>{dryingHour?.flag ?? "—"}</strong>
              </div>
            </div>
            <div class="life-bar-label">
              <span>Điểm thuận lợi</span>
              <span>
                {typeof laundry?.score === "number"
                  ? `${Math.round(laundry.score)}%`
                  : "—"}
              </span>
            </div>
            <div class="life-bar" aria-hidden="true">
              <span style={{ width: `${scoreWidth(laundry?.score)}%` }} />
            </div>
            <p class="life-tip">
              <span>Gợi ý: </span>
              {laundry?.message ?? "Chưa có câu đánh giá phơi đồ."}
            </p>
          </article>

          <article class="life-card">
            <header class="life-card-top">
              <div class="life-card-id">
                <span class="life-icon life-icon--shirt" aria-hidden="true">
                  ▢
                </span>
                <div>
                  <h3>Gợi ý trang phục</h3>
                  <p>Chưa có gợi ý theo nhiệt độ cảm nhận</p>
                </div>
              </div>
              <span class="life-badge life-badge--outfit">
                {day
                  ? `${roundOrDash(day.tempMin)}°C – ${roundOrDash(day.tempMax)}°C`
                  : "—"}
              </span>
            </header>
            <div class="life-outfit-row">
              <p>Ban ngày</p>
              <strong>—</strong>
            </div>
            <div class="life-outfit-row">
              <p>Chiều tối và đêm</p>
              <strong>—</strong>
            </div>
            <p class="life-tip">
              <span>Gợi ý: </span>
              Mục trang phục chưa nằm trong bản đánh giá, nên không gợi ý quần
              áo.
            </p>
          </article>

          <article class="life-card">
            <header class="life-card-top">
              <div class="life-card-id">
                <span class="life-icon life-icon--walk" aria-hidden="true">
                  👣
                </span>
                <div>
                  <h3>Khung giờ tập luyện</h3>
                  <p>Chưa có khung giờ khuyến nghị</p>
                </div>
              </div>
              <span class="life-badge">Chưa đánh giá</span>
            </header>
            <div class="life-highlight">
              <p>Khung giờ vàng khuyến nghị</p>
              <strong>—</strong>
            </div>
            <p class="life-tip">
              <span>Đánh giá: </span>
              Mục tập luyện chưa có trong dữ liệu đánh giá.
            </p>
          </article>

          <article class="life-card">
            <header class="life-card-top">
              <div class="life-card-id">
                <span class="life-icon life-icon--wash" aria-hidden="true">
                  🚗
                </span>
                <div>
                  <h3>Chỉ số rửa xe</h3>
                  <p>Điểm từ 3 giờ gần nhất</p>
                </div>
              </div>
              <span class="life-badge life-badge--wash">
                {typeof carWash?.score === "number"
                  ? `${Math.round(carWash.score)}/100`
                  : "—"}
              </span>
            </header>
            <div class="life-alert">
              <span>Khuyến nghị</span>
              <p>{carWash?.message ?? "Chưa có câu đánh giá rửa xe."}</p>
            </div>
            {upcoming.length > 0 && (
              <ul class="life-rain">
                {upcoming.map((item) => (
                  <li key={item.date}>
                    <span>
                      {item.date?.slice(8)}/{item.date?.slice(5, 7)}
                    </span>
                    <strong>
                      {typeof item.rain_sum === "number" ? item.rain_sum : "—"}{" "}
                      mm
                    </strong>
                  </li>
                ))}
              </ul>
            )}
          </article>
        </div>
      </section>
    </div>
  );
}
