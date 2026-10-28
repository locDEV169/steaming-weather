export function TopbarMeta({ data }) {
  const updatedAt = new Intl.DateTimeFormat("vi-VN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(data.current.time));

  return (
    <>
      <span class="live-dot" aria-hidden="true" />
      <span>Cập nhật {updatedAt}</span>
      <span class="meta-divider" aria-hidden="true" />
      <span>{data.timezone_abbreviation || data.timezone}</span>
    </>
  );
}
