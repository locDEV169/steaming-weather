export function TopbarMeta({ data }) {
  const date = new Date(data.current.time);
  if (Number.isNaN(date.getTime())) return null;
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");

  return (
    <p class="now-updated">
      <span class="live-dot" aria-hidden="true" />
      <span>
        Cập nhật lúc {hh}:{mm}, {dd}/{month}/{date.getFullYear()}
      </span>
    </p>
  );
}
