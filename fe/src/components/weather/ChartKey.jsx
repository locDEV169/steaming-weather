export function ChartKey({ mode }) {
  return (
    <div class="chart-key" aria-label="Chú giải biểu đồ">
      {mode !== "daily" && (
        <span class="key-item">
          <i class="key-line key-temperature" aria-hidden="true" />
          Nhiệt độ
        </span>
      )}
      {mode !== "hourly" && (
        <>
          <span class="key-item">
            <i class="key-bar" aria-hidden="true" />
            Lượng mưa
          </span>
          {mode === "overview" && (
            <>
              <span class="key-item">
                <i class="key-point key-max" aria-hidden="true" />
                Cao nhất
              </span>
              <span class="key-item">
                <i class="key-point key-min" aria-hidden="true" />
                Thấp nhất
              </span>
            </>
          )}
        </>
      )}
    </div>
  );
}
