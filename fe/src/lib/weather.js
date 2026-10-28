export const DATA_URL = "/api/v1/weather";

export const weatherDescriptions = {
  0: ["Nắng quang", "☀"],
  1: ["Ít mây", "◒"],
  2: ["Có mây", "☁"],
  3: ["Nhiều mây", "☁"],
  45: ["Sương mù", "≋"],
  48: ["Sương muối", "≋"],
  51: ["Mưa phùn nhẹ", "☂"],
  53: ["Mưa phùn", "☂"],
  55: ["Mưa phùn dày", "☂"],
  56: ["Mưa phùn đóng băng", "❄"],
  57: ["Mưa phùn đóng băng", "❄"],
  61: ["Mưa nhẹ", "☂"],
  63: ["Mưa vừa", "☂"],
  65: ["Mưa to", "☂"],
  66: ["Mưa đóng băng", "❄"],
  67: ["Mưa đóng băng", "❄"],
  71: ["Tuyết nhẹ", "❄"],
  73: ["Tuyết vừa", "❄"],
  75: ["Tuyết dày", "❄"],
  77: ["Hạt tuyết", "❄"],
  80: ["Mưa rào nhẹ", "☂"],
  81: ["Mưa rào", "☂"],
  82: ["Mưa rào lớn", "☂"],
  85: ["Mưa tuyết nhẹ", "❄"],
  86: ["Mưa tuyết dày", "❄"],
  95: ["Dông", "ϟ"],
  96: ["Dông, mưa đá nhẹ", "ϟ"],
  99: ["Dông, mưa đá", "ϟ"],
};

export function describeWeather(code) {
  return weatherDescriptions[code] ?? ["Chưa xác định", "·"];
}

export function timestampLabel(value, mode) {
  if (mode === "daily") {
    return new Intl.DateTimeFormat("vi-VN", {
      day: "numeric",
      month: "short",
    }).format(new Date(`${value}T12:00:00`));
  }

  const [date, time] = value.split("T");
  const hour = Number(time.slice(0, 2));
  if (hour === 0) {
    return new Intl.DateTimeFormat("vi-VN", {
      day: "numeric",
      month: "short",
    }).format(new Date(`${date}T12:00:00`));
  }
  return hour === 12 ? "12:00" : "";
}
