export function AirQualitySection({ airQuality, loading, error }) {
  const summary = airQuality?.results?.summary;
  const index = airQuality?.results?.overall?.index;
  const bandCode = summary?.band_code;
  const bandClass =
    bandCode != null ? `aq-panel aq-band--${bandCode}` : "aq-panel";

  return (
    <section
      class="forecast-section forecast-section--secondary"
      aria-labelledby="air-quality-title"
    >
      <div class="chart-header">
        <div>
          <p class="eyebrow chart-eyebrow">AIR QUALITY</p>
          <h2 id="air-quality-title">Chất lượng không khí</h2>
        </div>
      </div>

      <div class="chart-frame">
        {loading && (
          <div class="loading-state panel-state" role="status">
            Đang tải chất lượng không khí...
          </div>
        )}
        {error && (
          <div class="error-state panel-state" role="alert">
            {error}
          </div>
        )}
        {summary && (
          <div class={bandClass}>
            <div class="aq-primary">
              <p class="aq-index">
                {Math.round(index)}
                <span class="aq-index-unit"> EAQI</span>
              </p>
              <p class="aq-level">{summary.level_vi}</p>
            </div>
            <p class="aq-meaning">{summary.meaning_vi}</p>
          </div>
        )}
      </div>
      <p class="chart-footnote">European AQI · Open-Meteo · Đà Nẵng</p>
    </section>
  );
}
