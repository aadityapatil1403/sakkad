import type { BackendCapture, ReferenceMatch } from "../lib/types";

export const mockReferenceMatch: ReferenceMatch = {
  brand: "Rick Owens",
  title: "Drkshdw utility parka",
  score: 0.42,
  description: "Oversized structured outerwear with raw seams and dark palette.",
};

export const mockCapture: BackendCapture = {
  id: "test-capture-001",
  session_id: "session-abc",
  image_url: "https://example.com/test.jpg",
  created_at: "2026-04-24T10:00:00Z",
  taxonomy_matches: {
    "Quiet Luxury": 0.87,
    "Gorpcore": 0.12,
    "Concrete Brutalism": 0.05,
  },
  layer1_tags: ["black", "structured", "matte", "oversized", "leather"],
  layer2_tags: ["moto-collar", "raw-seam", "drop-shoulder", "zip-closure", "leather-panel"],
  tags: {
    palette: ["#1a1a1a", "#2d2d2d", "#8b7355"],
    attributes: ["structured", "dark"],
    mood: "austere",
    layer2: null,
  },
  reference_matches: [mockReferenceMatch],
  reference_explanation:
    "This image reads closest to Quiet Luxury and aligns with Drkshdw utility parka. Key visual cues include moto-collar, raw-seam, drop-shoulder.",
};

export const mockAbstractCapture: BackendCapture = {
  ...mockCapture,
  id: "test-capture-002",
  taxonomy_matches: {
    "Concrete Brutalism": 0.91,
    "Oxidized Metal": 0.23,
    "Quiet Luxury": 0.03,
  },
  layer1_tags: ["grey", "textured", "rough", "matte", "angular"],
  layer2_tags: ["cracked-surface", "mineral-wash", "matte-slate", "raw-grain", "dust-worn"],
  reference_explanation:
    "This image reads closest to Concrete Brutalism. Key visual cues include cracked-surface, mineral-wash, matte-slate.",
};
