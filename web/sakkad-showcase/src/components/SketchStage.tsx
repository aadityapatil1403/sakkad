interface Props {
  statement: string;
  onClose: () => void;
}

export function SketchStage({ statement, onClose }: Props) {
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
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-md)",
          maxWidth: 600,
          width: "100%",
          padding: 40,
        }}
      >
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
            Image generation requires a backend-proxied endpoint.
            <br />
            No Gemini key is exposed to the browser.
            <br />
            This stage will be enabled once{" "}
            <code
              style={{
                fontFamily: "var(--font-mono)",
                color: "var(--color-accent)",
                fontSize: 11,
              }}
            >
              POST /api/generate/image
            </code>{" "}
            is built.
          </div>
        </div>

        <button onClick={onClose}>← Back to relationships</button>
      </div>
    </div>
  );
}
