import type { BackendCapture } from "../lib/types";
import { formatDate, topTaxonomyLabel } from "../lib/format";

interface Props {
  capture: BackendCapture;
}

export function ImagePanel({ capture }: Props) {
  const palette = capture.tags?.palette ?? [];
  const topLabel = topTaxonomyLabel(capture.taxonomy_matches);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div
        style={{
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-sm)",
          overflow: "hidden",
          background: "var(--color-surface)",
        }}
      >
        <img
          src={capture.image_url}
          alt={topLabel ?? "Captured image"}
          style={{ width: "100%", maxHeight: "60vh", objectFit: "contain" }}
        />
      </div>

      {palette.length > 0 && (
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {palette.slice(0, 6).map((hex, i) => (
            <div
              key={i}
              title={hex}
              style={{
                width: 20,
                height: 20,
                borderRadius: "50%",
                background: hex,
                border: "1px solid var(--color-border)",
                flexShrink: 0,
              }}
            />
          ))}
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              color: "var(--color-text-dim)",
              marginLeft: 4,
            }}
          >
            palette
          </span>
        </div>
      )}

      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 10,
          color: "var(--color-text-dim)",
          letterSpacing: "0.04em",
        }}
      >
        {formatDate(capture.created_at)}
      </div>
    </div>
  );
}
