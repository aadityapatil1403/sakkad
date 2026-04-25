import { useState } from "react";
import type { BackendCapture, ReflectionResponse } from "../lib/types";
import { ScoreBar } from "./ScoreBar";

interface Props {
  capture: BackendCapture;
  onRequestReflection?: (sessionId: string) => Promise<ReflectionResponse>;
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

export function ReferencesPanel({ capture, onRequestReflection }: Props) {
  const [reflection, setReflection] = useState<ReflectionResponse | null>(null);
  const [reflectionLoading, setReflectionLoading] = useState(false);
  const [reflectionError, setReflectionError] = useState<string | null>(null);

  const references = capture.reference_matches ?? [];
  const top3 = references.slice(0, 3);

  async function handleReflection() {
    if (!capture.session_id || !onRequestReflection) return;
    setReflectionLoading(true);
    setReflectionError(null);
    try {
      const r = await onRequestReflection(capture.session_id);
      setReflection(r);
    } catch {
      setReflectionError("Reflection unavailable");
    } finally {
      setReflectionLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      <div>
        <SectionLabel>Designer References</SectionLabel>
        {top3.length === 0 ? (
          <p style={{ color: "var(--color-text-dim)", fontSize: 12 }}>
            No references matched
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {top3.map((ref, i) => {
              const weak = ref.score < 0.15;
              return (
                <div key={i} style={{ opacity: weak ? 0.4 : 1 }}>
                  <div
                    style={{
                      fontFamily: "var(--font-display)",
                      fontSize: 18,
                      fontWeight: 400,
                      color: "var(--color-text-primary)",
                      marginBottom: 2,
                    }}
                  >
                    {ref.brand}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 11,
                      color: "var(--color-text-muted)",
                      marginBottom: 8,
                    }}
                  >
                    {ref.title}
                  </div>
                  <ScoreBar label="" score={ref.score} delay={i * 120} />
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 11,
                      color: "var(--color-text-dim)",
                      lineHeight: 1.7,
                    }}
                  >
                    {ref.description}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {capture.reference_explanation && (
        <div>
          <SectionLabel>Classification</SectionLabel>
          <blockquote
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 17,
              fontStyle: "italic",
              fontWeight: 300,
              color: "var(--color-text-primary)",
              lineHeight: 1.7,
              borderLeft: "2px solid var(--color-accent)",
              paddingLeft: 16,
              margin: 0,
            }}
          >
            {capture.reference_explanation}
          </blockquote>
        </div>
      )}

      {capture.session_id && onRequestReflection && (
        <div>
          <SectionLabel>Session Reflection</SectionLabel>
          {reflection ? (
            <div>
              <blockquote
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: 17,
                  fontStyle: "italic",
                  fontWeight: 300,
                  color: "var(--color-text-primary)",
                  lineHeight: 1.7,
                  borderLeft: "2px solid var(--color-accent)",
                  paddingLeft: 16,
                  margin: 0,
                }}
              >
                {reflection.reflection}
              </blockquote>
              {reflection.fallback_used && (
                <div
                  style={{
                    marginTop: 8,
                    fontFamily: "var(--font-mono)",
                    fontSize: 10,
                    color: "var(--color-text-dim)",
                  }}
                >
                  deterministic fallback
                </div>
              )}
            </div>
          ) : reflectionError ? (
            <p style={{ color: "var(--color-error)", fontSize: 12 }}>
              {reflectionError}
            </p>
          ) : (
            <button
              className="primary"
              onClick={handleReflection}
              disabled={reflectionLoading}
            >
              {reflectionLoading
                ? "generating…"
                : "Generate Session Reflection →"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
