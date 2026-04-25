import type { HealthResponse } from "../lib/types";

interface Props {
  health: HealthResponse | null;
  loading: boolean;
  baseUrl: string;
}

export function StatusPill({ health, loading, baseUrl }: Props) {
  const ok = health?.status === "ok";
  const dot = loading ? "⊙" : ok ? "●" : "●";
  const label = loading
    ? "connecting"
    : ok
      ? "backend online"
      : "backend offline";
  const color = loading
    ? "var(--color-text-dim)"
    : ok
      ? "var(--color-accent)"
      : "var(--color-error)";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        color: "var(--color-text-muted)",
      }}
    >
      <span style={{ color, fontSize: 8 }}>{dot}</span>
      <span>{label}</span>
      <span style={{ color: "var(--color-text-dim)", marginLeft: 4 }}>
        {baseUrl}
      </span>
      {health?.taxonomy_labels && (
        <span style={{ color: "var(--color-text-dim)" }}>
          · {health.taxonomy_labels} labels
        </span>
      )}
    </div>
  );
}
