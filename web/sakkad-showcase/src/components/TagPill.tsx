interface Props {
  label: string;
  variant?: "layer1" | "layer2";
}

export function TagPill({ label, variant = "layer1" }: Props) {
  const isLayer2 = variant === "layer2";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        border: `1px solid ${isLayer2 ? "var(--color-accent-dim)" : "var(--color-border)"}`,
        borderRadius: "var(--radius-sm)",
        fontSize: 11,
        fontFamily: "var(--font-mono)",
        fontWeight: 300,
        color: isLayer2 ? "var(--color-accent)" : "var(--color-text-muted)",
        letterSpacing: "0.04em",
        whiteSpace: "nowrap",
      }}
    >
      {label}
    </span>
  );
}
