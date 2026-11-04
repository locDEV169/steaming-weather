export function PageShell({ meta, summary }) {
  return (
    <>
      <header class="topbar">
        <a class="wordmark" href="./" aria-label="Weather desk, trang chủ">
          <span class="wordmark-mark" aria-hidden="true">
            W
          </span>
          <span>
            WEATHER<span class="wordmark-light">DESK</span>
          </span>
        </a>
        <div class="topbar-meta">{meta}</div>
      </header>

      <section
        class="location-heading location-heading--slim"
        aria-labelledby="page-title"
      >
        <div class="location-heading-title">
          <p class="eyebrow">OPEN-METEO FORECAST</p>
          <h1 id="page-title">
            Đà Nẵng <span class="heading-coordinate">16.06°N 108.24°E</span>
          </h1>
          <p class="location-subtitle">Dự báo thời tiết · Việt Nam</p>
        </div>
        {summary ? (
          <div class="location-heading-summary" aria-live="polite">
            {summary}
          </div>
        ) : null}
      </section>
    </>
  );
}
