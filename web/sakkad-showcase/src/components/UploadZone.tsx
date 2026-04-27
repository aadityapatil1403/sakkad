import { useRef, useState } from "react";
import { PipelineReveal } from "./PipelineReveal";

interface Props {
  onUpload: (file: File) => Promise<void>;
  loading: boolean;
  error: string | null;
}

export function UploadZone({ onUpload, loading, error }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [pipelineActive, setPipelineActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    if (!file.type.startsWith("image/")) return;
    const url = URL.createObjectURL(file);
    setPreview(url);
    setPipelineActive(true);
    await onUpload(file);
    setPipelineActive(false);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) void handleFile(file);
  }

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) void handleFile(file);
    e.target.value = "";
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
  }

  const borderColor = error
    ? "var(--color-error-border)"
    : dragOver
      ? "var(--color-accent)"
      : "var(--color-border)";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload image for classification"
        onDrop={onDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => !loading && inputRef.current?.click()}
        onKeyDown={onKeyDown}
        style={{
          border: `1px dashed ${borderColor}`,
          borderRadius: "var(--radius-sm)",
          minHeight: preview ? "auto" : 320,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          cursor: loading ? "wait" : "pointer",
          transition: "border-color 150ms",
          overflow: "hidden",
          background: dragOver
            ? "var(--color-accent-dim)"
            : "var(--color-surface)",
          transform: dragOver ? "scale(1.01)" : "scale(1)",
        }}
      >
        {preview ? (
          <img
            src={preview}
            alt="Upload preview"
            style={{ width: "100%", maxHeight: 400, objectFit: "contain" }}
          />
        ) : (
          <div style={{ textAlign: "center", padding: 40 }}>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 48,
                fontWeight: 300,
                letterSpacing: "0.2em",
                color: "var(--color-text-dim)",
                marginBottom: 12,
              }}
            >
              SAKKAD
            </div>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 12,
                color: "var(--color-text-dim)",
                letterSpacing: "0.06em",
              }}
            >
              Drop an image. Watch it think.
            </div>
          </div>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={onInputChange}
        aria-label="File input for image upload"
      />

      {error && (
        <div
          style={{
            marginTop: 8,
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            color: "var(--color-error)",
            border: "1px solid var(--color-error-border)",
            padding: "6px 10px",
            borderRadius: "var(--radius-sm)",
          }}
        >
          {error}
        </div>
      )}

      <div style={{ marginTop: 12 }}>
        <button
          className="primary"
          onClick={() => !loading && inputRef.current?.click()}
          disabled={loading}
          style={{ width: "100%" }}
        >
          {loading ? "Uploading…" : "Upload Image"}
        </button>
      </div>

      <PipelineReveal active={pipelineActive} />
    </div>
  );
}
