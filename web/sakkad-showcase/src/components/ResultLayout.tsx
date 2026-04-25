import type { BackendCapture, ReflectionResponse } from "../lib/types";
import { ImagePanel } from "./ImagePanel";
import { TaxonomyPanel } from "./TaxonomyPanel";
import { ReferencesPanel } from "./ReferencesPanel";

interface Props {
  capture: BackendCapture;
  onRequestReflection: (sessionId: string) => Promise<ReflectionResponse>;
}

export function ResultLayout({ capture, onRequestReflection }: Props) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "35% 35% 30%",
        gap: 0,
        minHeight: 0,
      }}
    >
      <div
        style={{ padding: 24, borderRight: "1px solid var(--color-border)" }}
      >
        <ImagePanel capture={capture} />
      </div>
      <div
        style={{
          padding: 24,
          borderRight: "1px solid var(--color-border)",
          overflowY: "auto",
        }}
      >
        <TaxonomyPanel capture={capture} />
      </div>
      <div style={{ padding: 24, overflowY: "auto" }}>
        <ReferencesPanel
          capture={capture}
          onRequestReflection={onRequestReflection}
        />
      </div>
    </div>
  );
}
