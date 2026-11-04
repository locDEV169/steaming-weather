export function RainChartKey() {
  return (
    <div class="chart-key" aria-label="Chú giải biểu đồ mưa">
      <span class="key-item">
        <i class="key-bar key-rain-past" aria-hidden="true" />
        Quá khứ
      </span>
      <span class="key-item">
        <i class="key-bar key-rain-current" aria-hidden="true" />
        Hiện tại
      </span>
      <span class="key-item">
        <i class="key-bar key-rain-future" aria-hidden="true" />
        Dự báo
      </span>
    </div>
  );
}
