import { useState } from "react";
import type { BackendCapture, GenerateResponse } from "../lib/types";
import {
  aggregateGroupTaxonomy,
  aggregateGroupTags,
  sortedTaxonomy,
} from "../lib/format";
import { generateCopy } from "../lib/api";
import { TagPill } from "./TagPill";
import { ScoreBar } from "./ScoreBar";

interface Props {
  captures: BackendCapture[];
  onSelectStatement: (statement: string) => void;
  onClose: () => void;
}

const KINDS: GenerateResponse["kind"][] = [
  "creative_summary",
  "styling_direction",
  "inspiration_prompt",
];

function buildFallbackStatement(captures: BackendCapture[]): string {
  const { layer2, references } = aggregateGroupTags(captures);
  const agg = aggregateGroupTaxonomy(captures);
  const topLabel = sortedTaxonomy(agg)[0]?.[0] ?? "this aesthetic";
  const cues = layer2.slice(0, 3).join(", ");
  const ref = references[0] ? ` Echoes of ${references[0]}.` : "";
  return `A visual tension rooted in ${topLabel}${cues ? ` — ${cues}` : ""}.${ref}`;
}

export function RelationshipPanel({
  captures,
  onSelectStatement,
  onClose,
}: Props) {
  const [statements, setStatements] = useState<
    { text: string; fallback: boolean }[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  const aggregatedTaxonomy = sortedTaxonomy(
    aggregateGroupTaxonomy(captures),
  ).slice(0, 5);
  const { layer1, layer2, references } = aggregateGroupTags(captures);
  const captureIds = captures.map((c) => c.id);

  async function handleGenerate() {
    setLoading(true);
    setStatements([]);
    const results: { text: string; fallback: boolean }[] = [];

    for (const kind of KINDS) {
      try {
        const r = await generateCopy(kind, { capture_ids: captureIds });
        results.push({ text: r.text, fallback: r.fallback_used });
      } catch {
        // keep going — partial results are fine
      }
    }

    if (results.length === 0) {
      results.push({ text: buildFallbackStatement(captures), fallback: true });
    }

    setStatements(results);
    setLoading(false);
  }

  function handleSelect(idx: number) {
    setSelectedIdx(idx);
    onSelectStatement(statements[idx]!.text);
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.85)",
        zIndex: 100,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
      }}
    >
      <div
        style={{
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-md)",
          width: "100%",
          maxWidth: 1100,
          maxHeight: "90vh",
          overflow: "auto",
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
        }}
      >
        {/* Col 1 — Suggested Relationships */}
        <div
          style={{ padding: 28, borderRight: "1px solid var(--color-border)" }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 20,
            }}
          >
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                color: "var(--color-text-dim)",
              }}
            >
              Suggested Relationships
            </div>
            <button
              onClick={onClose}
              style={{
                border: "none",
                padding: "2px 8px",
                fontSize: 16,
                color: "var(--color-text-dim)",
              }}
            >
              ×
            </button>
          </div>

          {statements.length === 0 && !loading && (
            <button
              className="primary"
              onClick={handleGenerate}
              disabled={captures.length < 1}
            >
              Generate Relationships →
            </button>
          )}

          {loading && (
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                color: "var(--color-text-dim)",
              }}
            >
              Generating…
            </div>
          )}

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 10,
              marginTop: 12,
            }}
          >
            {statements.map((s, i) => (
              <div
                key={i}
                onClick={() => handleSelect(i)}
                style={{
                  padding: 12,
                  border: `1px solid ${selectedIdx === i ? "var(--color-accent)" : "var(--color-border)"}`,
                  borderRadius: "var(--radius-sm)",
                  cursor: "pointer",
                  background:
                    selectedIdx === i
                      ? "var(--color-accent-dim)"
                      : "transparent",
                  transition: "border-color 150ms, background 150ms",
                }}
              >
                <p
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 14,
                    fontStyle: "italic",
                    color: "var(--color-text-primary)",
                    lineHeight: 1.6,
                    margin: 0,
                  }}
                >
                  {s.text}
                </p>
                {s.fallback && (
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 10,
                      color: "var(--color-text-dim)",
                      marginTop: 6,
                    }}
                  >
                    deterministic fallback
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Col 2 — Grouped Images */}
        <div
          style={{ padding: 28, borderRight: "1px solid var(--color-border)" }}
        >
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--color-text-dim)",
              marginBottom: 20,
            }}
          >
            Grouped Images ({captures.length})
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {captures.map((c) => (
              <div
                key={c.id}
                style={{ display: "flex", gap: 10, alignItems: "center" }}
              >
                <img
                  src={c.image_url}
                  alt=""
                  style={{
                    width: 64,
                    height: 64,
                    objectFit: "cover",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--color-border)",
                    flexShrink: 0,
                  }}
                />
                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-display)",
                      fontSize: 13,
                      color: "var(--color-text-primary)",
                    }}
                  >
                    {Object.keys(c.taxonomy_matches)[0] ?? "—"}
                  </div>
                  {c.layer2_tags?.[0] && (
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 10,
                        color: "var(--color-text-dim)",
                        marginTop: 2,
                      }}
                    >
                      {c.layer2_tags[0]}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Col 3 — Tags & Taxonomy */}
        <div style={{ padding: 28 }}>
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--color-text-dim)",
              marginBottom: 20,
            }}
          >
            Tags & Taxonomy
          </div>

          {aggregatedTaxonomy.length > 0 && (
            <div style={{ marginBottom: 24 }}>
              {aggregatedTaxonomy.map(([label, score], i) => (
                <ScoreBar
                  key={label}
                  label={label}
                  score={score}
                  delay={i * 80}
                />
              ))}
            </div>
          )}

          {references.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 10,
                  color: "var(--color-text-dim)",
                  marginBottom: 8,
                }}
              >
                References
              </div>
              {references.map((r) => (
                <div
                  key={r}
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 13,
                    color: "var(--color-text-muted)",
                    marginBottom: 4,
                  }}
                >
                  {r}
                </div>
              ))}
            </div>
          )}

          {layer2.length > 0 && (
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 6,
                marginBottom: 12,
              }}
            >
              {layer2.slice(0, 12).map((t) => (
                <TagPill key={t} label={t} variant="layer2" />
              ))}
            </div>
          )}

          {layer1.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {layer1.slice(0, 10).map((t) => (
                <TagPill key={t} label={t} variant="layer1" />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
