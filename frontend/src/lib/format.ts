export function formatNumber(value?: number | null): string {
  if (value === null || value === undefined) return "Unavailable";
  return new Intl.NumberFormat("en", { notation: value >= 1000000 ? "compact" : "standard" }).format(value);
}

export function formatPercent(value?: number | null): string {
  if (value === null || value === undefined) return "Unavailable";
  return `${value.toFixed(2)}%`;
}

export function formatDuration(seconds?: number | null): string {
  if (seconds === null || seconds === undefined) return "Unavailable";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${String(secs).padStart(2, "0")}`;
}

export function formatDate(value?: string | null): string {
  if (!value) return "Unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(date);
}
