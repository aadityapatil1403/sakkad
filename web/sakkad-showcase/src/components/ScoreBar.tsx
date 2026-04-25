import { useEffect, useState } from "react";

interface Props {
  score: number;
  delay?: number;
  label: string;
  sublabel?: string;
}

export function ScoreBar({ score, delay = 0, label, sublabel }: Props) {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const t = setTimeout(() => setWidth(score * 100), delay);
    return () => clearTimeout(t);
  }, [score, delay]);

  return (
    <div style={{ marginBottom: 12 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: 4,
        }}
      >
        <div>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 15,
              fontWeight: 400,
              color: "var(--color-text-primary)",
            }}
          >
            {label}
          </span>
          {sublabel && (
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                color: "var(--color-text-dim)",
                marginLeft: 8,
                letterSpacing: "0.06em",
                textTransform: "uppercase",
              }}
            >
              {sublabel}
            </span>
          )}
        </div>
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            color: "var(--color-text-muted)",
          }}
        >
          {(score * 100).toFixed(0)}%
        </span>
      </div>
      <div
        style={{
          height: 2,
          background: "var(--color-border)",
          borderRadius: 1,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${width}%`,
            background: "var(--color-accent)",
            borderRadius: 1,
            transition: "width 700ms cubic-bezier(0.25, 0, 0, 1)",
          }}
        />
      </div>
    </div>
  );
}
