import type { BackendCapture } from "../lib/types";
import { topTaxonomyLabel } from "../lib/format";

interface Props {
  captures: BackendCapture[];
  activeId: string | null;
  selectedIds: Set<string>;
  onSelect: (capture: BackendCapture) => void;
  loading: boolean;
}

export function GalleryStrip({
  captures,
  activeId,
  selectedIds,
  onSelect,
  loading,
}: Props) {
  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            style={{
              height: 80,
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-sm)",
              animation: "pulse 1.5s ease-in-out infinite",
            }}
          />
        ))}
      </div>
    );
  }

  if (captures.length === 0) {
    return (
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          color: "var(--color-text-dim)",
          padding: "20px 0",
        }}
      >
        No captures yet. Upload an image to begin.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 10,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          color: "var(--color-text-dim)",
          marginBottom: 8,
          paddingBottom: 6,
          borderBottom: "1px solid var(--color-border)",
        }}
      >
        Recent captures
      </div>
      {captures.slice(0, 8).map((c) => {
        const isActive = c.id === activeId;
        const isSelected = selectedIds.has(c.id);
        const topLabel = topTaxonomyLabel(c.taxonomy_matches);
        return (
          <button
            key={c.id}
            onClick={() => onSelect(c)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: 8,
              border: `1px solid ${isSelected || isActive ? "var(--color-accent)" : "var(--color-border)"}`,
              borderRadius: "var(--radius-sm)",
              background:
                isSelected || isActive
                  ? "var(--color-accent-dim)"
                  : "transparent",
              cursor: "pointer",
              textAlign: "left",
              width: "100%",
              transition: "border-color 150ms, background 150ms",
            }}
          >
            <div style={{ position: "relative", flexShrink: 0 }}>
              <img
                src={c.image_url}
                alt={topLabel ?? "Capture"}
                style={{
                  width: 52,
                  height: 52,
                  objectFit: "cover",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--color-border)",
                  display: "block",
                }}
              />
              {isSelected && (
                <div
                  style={{
                    position: "absolute",
                    top: 3,
                    right: 3,
                    width: 16,
                    height: 16,
                    background: "var(--color-accent)",
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 9,
                    color: "#0a0a0a",
                    fontWeight: 700,
                    lineHeight: 1,
                  }}
                >
                  ✓
                </div>
              )}
            </div>
            <div style={{ overflow: "hidden" }}>
              <div
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: 13,
                  color: isActive
                    ? "var(--color-accent)"
                    : "var(--color-text-primary)",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {topLabel ?? "—"}
              </div>
              {c.reference_matches?.[0] && (
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 10,
                    color: "var(--color-text-dim)",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {c.reference_matches[0].brand}
                </div>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}
