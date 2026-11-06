export function PageShell({ updated, chips, summary }) {
  return (
    <>
      <section
        class="location-heading location-heading--slim"
        aria-labelledby="page-title"
      >
        <div class="now-heading-row">
          <div class="location-heading-title">
            <h1 class="now-place" id="page-title">
              <span class="now-pin" aria-hidden="true">
                <svg viewBox="0 0 24 24" width="16" height="16">
                  <path
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.8"
                    d="M12 21s6-5.2 6-10a6 6 0 1 0-12 0c0 4.8 6 10 6 10z"
                  />
                  <circle
                    cx="12"
                    cy="11"
                    r="2.2"
                    fill="currentColor"
                    stroke="none"
                  />
                </svg>
              </span>
              Đà Nẵng, Việt Nam
            </h1>
            {updated}
          </div>
          {chips}
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
