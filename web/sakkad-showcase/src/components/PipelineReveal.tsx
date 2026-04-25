import { useEffect, useState } from "react";

const STAGES = [
  "Image uploaded to storage",
  "SigLIP embedding computed (768-dim)",
  "Taxonomy classified against 81 labels",
  "Designer references matched (74 entries)",
  "Color palette extracted",
  "Layer 1 tags generated (Gemini)",
  "Layer 2 tags generated (Gemini)",
  "Narrative explanation written",
];

interface Props {
  active: boolean;
  onComplete?: () => void;
}

export function PipelineReveal({ active, onComplete }: Props) {
  const [revealed, setRevealed] = useState(0);

  useEffect(() => {
    if (!active) {
      setRevealed(0);
      return;
    }
    let i = 0;
    const interval = setInterval(() => {
      i += 1;
      setRevealed(i);
      if (i >= STAGES.length) {
        clearInterval(interval);
        onComplete?.();
      }
    }, 400);
    return () => clearInterval(interval);
  }, [active, onComplete]);

  if (!active && revealed === 0) return null;

  return (
    <div
      style={{
        marginTop: 24,
        fontFamily: "var(--font-mono)",
        fontSize: 11,
        color: "var(--color-text-muted)",
        lineHeight: 2,
      }}
    >
      {STAGES.slice(0, revealed).map((stage, i) => (
        <div
          key={i}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            opacity: i < revealed - 1 ? 0.5 : 1,
            transition: "opacity 300ms",
          }}
        >
          <span style={{ color: "var(--color-accent)", fontSize: 10 }}>✓</span>
          {stage}
        </div>
      ))}
      {active && revealed < STAGES.length && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            color: "var(--color-text-dim)",
          }}
        >
          <span style={{ animation: "pulse 1s infinite" }}>·</span>
          {STAGES[revealed]}
        </div>
      )}
    </div>
  );
}
