export interface ReferenceMatch {
  brand: string;
  title: string;
  score: number;
  description: string;
}

export interface CaptureTags {
  palette: string[] | null;
  attributes: string[] | null;
  mood: string | null;
  layer2: string[] | null;
}

export interface BackendCapture {
  id: string;
  session_id: string | null;
  image_url: string;
  created_at: string;
  taxonomy_matches: Record<string, number>;
  layer1_tags: string[] | null;
  layer2_tags: string[] | null;
  tags: CaptureTags;
  reference_matches: ReferenceMatch[] | null;
  reference_explanation: string | null;
}

export interface ReflectionResponse {
  session_id: string;
  reflection: string;
  fallback_used: boolean;
  capture_count: number;
}

export interface GenerateResponse {
  kind: "inspiration_prompt" | "styling_direction" | "creative_summary";
  text: string;
  fallback_used: boolean;
  source: { session_id?: string; capture_ids?: string[] };
}

export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  database?: string;
  storage?: string;
  taxonomy?: string;
  taxonomy_labels?: number;
}

export interface ApiError {
  message: string;
  status: number;
}

export interface GenerateImageResponse {
  image_b64: string;
  mime_type: string;
  statement: string;
  taxonomy_influences: Array<{ label: string; score: number }>;
}

// Abstract visual taxonomy labels — used to detect is_abstract path for layer2 display
export const ABSTRACT_VISUAL_LABELS = new Set([
  "Botanical Organic",
  "Fluid Bloom",
  "Cellular Pattern",
  "Raw Fiber",
  "Veined Leaf",
  "Concrete Brutalism",
  "Oxidized Metal",
  "Raw Utility",
  "Exposed Structure",
  "Hardline Framework",
  "Woven Surface",
  "Patinated Finish",
  "Eroded Edge",
  "Layered Grain",
  "Frayed Composite",
  "Earth Palette",
  "Monochrome Field",
  "Luminous Gradient",
  "Muted Wash",
  "Dusty Contrast",
  "Neon Lit Night",
  "Wet Pavement",
  "Geometric Tile",
  "Weathered Signage",
  "Transit Glow",
]);

export function isAbstractCapture(capture: BackendCapture): boolean {
  const topLabel = Object.keys(capture.taxonomy_matches)[0];
  return topLabel !== undefined && ABSTRACT_VISUAL_LABELS.has(topLabel);
}
