import { useEffect, useRef, useState } from "react";
import type {
  BackendCapture,
  HealthResponse,
  ReflectionResponse,
} from "./lib/types";
import { getHealth, getGallery, uploadCapture } from "./lib/api";
import { StatusPill } from "./components/StatusPill";
import { UploadZone } from "./components/UploadZone";
import { GalleryStrip } from "./components/GalleryStrip";
import { ResultLayout } from "./components/ResultLayout";
import { RelationshipPanel } from "./components/RelationshipPanel";
import { SketchStage } from "./components/SketchStage";

const BASE_URL =
  (import.meta.env["VITE_BACKEND_URL"] as string | undefined) ??
  "http://127.0.0.1:8000";

async function fetchReflection(sessionId: string): Promise<ReflectionResponse> {
  const res = await fetch(`${BASE_URL}/api/sessions/${sessionId}/reflection`, {
    headers: { "ngrok-skip-browser-warning": "true" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<ReflectionResponse>;
}

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [gallery, setGallery] = useState<BackendCapture[]>([]);
  const [galleryLoading, setGalleryLoading] = useState(true);
  const [active, setActive] = useState<BackendCapture | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [selectedCaptures, setSelectedCaptures] = useState<BackendCapture[]>(
    [],
  );
  const [showRelationships, setShowRelationships] = useState(false);
  const [sketchStatement, setSketchStatement] = useState<string | null>(null);
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    void (async () => {
      try {
        const h = await getHealth();
        setHealth(h);
      } catch {
        setHealth({ status: "error" });
      } finally {
        setHealthLoading(false);
      }

      try {
        const captures = await getGallery();
        setGallery(captures);
        if (captures.length > 0) setActive(captures[0] ?? null);
      } catch {
        // gallery failure is non-fatal
      } finally {
        setGalleryLoading(false);
      }
    })();
  }, []);

  async function handleUpload(file: File) {
    setUploading(true);
    setUploadError(null);
    try {
      const capture = await uploadCapture(file);
      setGallery((prev) => [capture, ...prev]);
      setActive(capture);
    } catch {
      setUploadError("Upload failed. Check that the backend is running.");
    } finally {
      setUploading(false);
    }
  }

  function toggleSelected(capture: BackendCapture) {
    setSelectedCaptures((prev) =>
      prev.find((c) => c.id === capture.id)
        ? prev.filter((c) => c.id !== capture.id)
        : [...prev, capture],
    );
  }

  function handleSelectStatement(statement: string) {
    setSketchStatement(statement);
    setShowRelationships(false);
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "var(--color-bg)",
      }}
    >
      {/* Header */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 28px",
          borderBottom: "1px solid var(--color-border)",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 22,
            fontWeight: 300,
            letterSpacing: "0.22em",
            color: "var(--color-text-primary)",
          }}
        >
          SAKKAD
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          {selectedCaptures.length >= 1 && (
            <button
              className="primary"
              onClick={() => setShowRelationships(true)}
            >
              Explore Relationships ({selectedCaptures.length}) →
            </button>
          )}
          <StatusPill
            health={health}
            loading={healthLoading}
            baseUrl={BASE_URL}
          />
        </div>
      </header>

      {/* Main */}
      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
        }}
      >
        {/* Top: upload + gallery */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "60% 40%",
            borderBottom: "1px solid var(--color-border)",
          }}
        >
          <div
            style={{
              padding: 28,
              borderRight: "1px solid var(--color-border)",
            }}
          >
            <UploadZone
              onUpload={handleUpload}
              loading={uploading}
              error={uploadError}
            />
          </div>
          <div style={{ padding: 28, overflowY: "auto", maxHeight: 480 }}>
            <GalleryStrip
              captures={gallery}
              activeId={active?.id ?? null}
              onSelect={(c) => {
                setActive(c);
                toggleSelected(c);
              }}
              loading={galleryLoading}
            />
          </div>
        </div>

        {/* Bottom: result */}
        {active ? (
          <div style={{ flex: 1, overflowY: "auto" }}>
            <ResultLayout
              capture={active}
              onRequestReflection={fetchReflection}
            />
          </div>
        ) : (
          <div
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: "var(--font-display)",
              fontSize: 18,
              fontStyle: "italic",
              color: "var(--color-text-dim)",
            }}
          >
            Upload an image or select a capture to begin.
          </div>
        )}
      </main>

      {/* Modals */}
      {showRelationships && selectedCaptures.length > 0 && (
        <RelationshipPanel
          captures={selectedCaptures}
          onSelectStatement={handleSelectStatement}
          onClose={() => setShowRelationships(false)}
        />
      )}

      {sketchStatement && (
        <SketchStage
          statement={sketchStatement}
          captureIds={selectedCaptures.map((c) => c.id)}
          onClose={() => setSketchStatement(null)}
        />
      )}
    </div>
  );
}
