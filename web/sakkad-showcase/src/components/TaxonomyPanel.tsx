import type { BackendCapture } from "../lib/types";
import { sortedTaxonomy, isAbstractCapture } from "../lib/format";
import { ScoreBar } from "./ScoreBar";
import { TagPill } from "./TagPill";

interface Props {
  capture: BackendCapture;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: 10,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        color: "var(--color-text-dim)",
        marginBottom: 12,
        paddingBottom: 6,
        borderBottom: "1px solid var(--color-border)",
      }}
    >
      {children}
    </div>
  );
}

export function TaxonomyPanel({ capture }: Props) {
  const topFive = sortedTaxonomy(capture.taxonomy_matches).slice(0, 5);
  const isAbstract = isAbstractCapture(capture);
  const layer1 = capture.layer1_tags ?? [];
  const layer2 = capture.layer2_tags ?? [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      <div>
        <SectionLabel>Taxonomy</SectionLabel>
        {topFive.length === 0 ? (
          <p style={{ color: "var(--color-text-dim)", fontSize: 12 }}>
            No taxonomy data
          </p>
        ) : (
          topFive.map(([label, score], i) => (
            <ScoreBar key={label} label={label} score={score} delay={i * 80} />
          ))
        )}
      </div>

      <div>
        <SectionLabel>Layer 1 — Visual Facts</SectionLabel>
        {layer1.length === 0 ? (
          <p style={{ color: "var(--color-text-dim)", fontSize: 12 }}>
            Unavailable
          </p>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {layer1.map((tag) => (
              <TagPill key={tag} label={tag} variant="layer1" />
            ))}
          </div>
        )}
      </div>

      <div>
        <SectionLabel>
          {isAbstract
            ? "Layer 2 — Material Language"
            : "Layer 2 — Fashion Descriptors"}
        </SectionLabel>
        {layer2.length === 0 ? (
          <p style={{ color: "var(--color-text-dim)", fontSize: 12 }}>
            Unavailable
          </p>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {layer2.map((tag) => (
              <TagPill key={tag} label={tag} variant="layer2" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
