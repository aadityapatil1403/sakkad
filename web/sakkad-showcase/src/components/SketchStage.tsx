import { useState } from "react";
import type { ReactElement } from "react";
import { generateImage } from "../lib/api";
import type { GenerateImageResponse } from "../lib/types";

interface Props {
  statement: string;
  captureIds: string[];
  onClose: () => void;
}

type State =
  | { phase: "idle" }
  | { phase: "loading" }
  | { phase: "done"; result: GenerateImageResponse }
  | { phase: "error"; message: string };

export function SketchStage({
  statement,
  captureIds,
  onClose,
}: Props): ReactElement {
  const [state, setState] = useState<State>({ phase: "idle" });

  async function handleGenerate(): Promise<void> {
    setState({ phase: "loading" });
    try {
      const result = await generateImage(statement, captureIds);
      setState({ phase: "done", result });
    } catch {
      setState({
        phase: "error",
        message: "Sketch generation failed. Please try again.",
      });
    }
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.92)",
        zIndex: 200,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 40,
      }}
    >
      <div
        style={{
          position: "relative",
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-md)",
          maxWidth: 600,
          maxHeight: "90vh",
          overflowY: "auto",
          width: "100%",
          padding: 40,
        }}
      >
        <button
          onClick={onClose}
          aria-label="Close"
          style={{
            position: "absolute",
            top: 16,
            right: 16,
            background: "none",
            border: "none",
            color: "var(--color-text-dim)",
            fontSize: 20,
            cursor: "pointer",
            lineHeight: 1,
            padding: 4,
          }}
        >
          ×
        </button>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 10,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: "var(--color-text-dim)",
            marginBottom: 24,
          }}
        >
          Sketch Stage
        </div>

        <blockquote
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 20,
            fontStyle: "italic",
            fontWeight: 300,
            color: "var(--color-text-primary)",
            lineHeight: 1.65,
            borderLeft: "2px solid var(--color-accent)",
            paddingLeft: 20,
            margin: "0 0 32px",
          }}
        >
          {statement}
        </blockquote>

        {state.phase === "idle" && (
          <div style={{ textAlign: "center", marginBottom: 24 }}>
            <button
              onClick={() => void handleGenerate()}
              style={{ padding: "12px 32px", fontSize: 14 }}
            >
              Generate Sketch →
            </button>
          </div>
        )}

        {state.phase === "loading" && (
          <div
            style={{
              border: "1px dashed var(--color-border)",
              borderRadius: "var(--radius-sm)",
              padding: "32px 24px",
              textAlign: "center",
              marginBottom: 24,
            }}
          >
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 28,
                fontWeight: 300,
                color: "var(--color-text-dim)",
                letterSpacing: "0.15em",
                marginBottom: 12,
              }}
            >
              GENERATING SKETCH…
            </div>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 11,
                color: "var(--color-text-dim)",
                lineHeight: 1.7,
              }}
            >
              This may take up to 30 seconds.
            </div>
          </div>
        )}

        {state.phase === "done" && (
          <div style={{ marginBottom: 24 }}>
            <img
              src={`data:${state.result.mime_type};base64,${state.result.image_b64}`}
              alt="Generated fashion sketch"
              style={{ width: "100%", borderRadius: "var(--radius-sm)" }}
            />
          </div>
        )}

        {state.phase === "error" && (
          <div
            style={{
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-sm)",
              padding: "24px",
              textAlign: "center",
              marginBottom: 24,
              color: "var(--color-text-dim)",
              fontFamily: "var(--font-mono)",
              fontSize: 12,
            }}
          >
            {state.message}
            <div style={{ marginTop: 16 }}>
              <button onClick={() => void handleGenerate()}>Retry →</button>
            </div>
          </div>
        )}

        <button onClick={onClose}>← Back to relationships</button>
      </div>
    </div>
  );
}
