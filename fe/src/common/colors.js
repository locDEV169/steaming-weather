/** Series colors shared by the chart configs and the legend CSS tokens. */
export const seriesColors = {
  temperature: "#43c6e8",
  temperatureFill: "rgba(67, 198, 232, 0.08)",
  rain: "#ff744d",
  rainBar: "rgba(255, 116, 77, 0.88)",
  rainBarDaily: "rgba(255, 116, 77, 0.82)",
  max: "#7898ce",
  min: "#e78bd1",
  axis: "#aebbc5",
  grid: "rgba(195, 209, 220, 0.18)",
  rainPast: "rgba(120, 152, 206, 0.85)",
  rainCurrent: "rgba(255, 116, 77, 0.92)",
  rainFuture: "rgba(67, 198, 232, 0.85)",
};

const seriesTokens = {
  "--cyan": seriesColors.temperature,
  "--orange": seriesColors.rain,
  "--blue": seriesColors.max,
  "--coral": seriesColors.min,
};

export function applySeriesColors(root = document.documentElement) {
  for (const [name, value] of Object.entries(seriesTokens)) {
    root.style.setProperty(name, value);
  }
}
