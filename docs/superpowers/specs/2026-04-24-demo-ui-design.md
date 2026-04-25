# Sakkad Demo UI — Design Spec

**Date:** 2026-04-24  
**Mode:** Marketing / Expressive — Luxury Minimal visual system  
**Purpose:** Standalone demo app showcasing the Sakkad backend's full classification pipeline. Target audience: demo viewers, Snap judges, fashion design students. Goal: make the backend's capabilities feel tangible and impressive in a single browser session.

---

## What This Is

A standalone React/Vite app at `sakad-backend/demo/` that calls the local FastAPI backend (`http://127.0.0.1:8000`). It has two modes of operation:

1. **Upload mode** — drag or pick an image, watch the full enrichment pipeline run live, see every output layer rendered
2. **Gallery mode** — browse all previously classified captures from `GET /api/gallery`, click any to see its full classification breakdown

The app is intentionally a **showcase**, not a workflow tool. It should feel like a museum exhibit about the backend's intelligence.

---

## Visual System: Luxury Minimal (Fashion Archive)

- **Background:** Near-black (`#0a0a0a`), raw paper texture as subtle overlay
- **Typography:** Display — `Cormorant Garamond` (editorial, fashion-archive weight). Body — `DM Mono` (technical precision, shows taxonomy scores and tag lists cleanly)
- **Accent:** Single warm tone — aged amber `#c9a96e` for scores, highlights, active states
- **Motion:** Slow, deliberate. 600–800ms ease-out reveals. No bounce, no spring. Page load stagger, left-to-right panel cascade.
- **Layout:** Asymmetric. Left-heavy. Generous negative space. No centered-everything.
- **One unforgettable thing:** The taxonomy score bars animate from 0 on first render — each bar fills with a different delay, like a spectrograph reading coming to life.

---

## Backend Pipeline (what the UI must surface)

Understanding the actual pipeline is essential to designing the right UI. The `POST /api/capture` flow:

```
Image upload
  → Supabase Storage (captures bucket)
  → SigLIP embedding (768-dim vector)
  → classify() → taxonomy_matches (top labels, 0–1 scores)
  → get_reference_matches() → reference_matches (designer corpus, 74 entries)
  → extract_palette() → tags.palette (hex colors)
  → get_layer1_tags() [Gemini] → layer1_tags (10 single-word visual facts)
  → get_layer2_tags() [Gemini, uses layer1] → layer2_tags (10 hyphenated fashion descriptors)
    - Abstract visual path: layer2_abstract_prompt (texture/material language)
    - Fashion path: layer2_fashion_prompt (garment/silhouette language)
  → generate_reference_explanation() → reference_explanation (narrative string)
  → Supabase insert
```

The UI reveals this pipeline **stage by stage** during processing, so the viewer sees the intelligence building up.

---

## Screen Architecture

### Screen 1: Upload / Home

**Layout:** Full viewport. Left 60% = drop zone. Right 40% = recent gallery strip (last 6 captures from `GET /api/gallery`).

**Drop zone states:**

- Idle: large dashed border, `SAKKAD` wordmark centered, subtitle "Drop an image. Watch it think."
- Drag-over: border glows amber, subtle scale up
- Processing: image preview fills the zone, pipeline stages animate in below (see Pipeline Reveal)
- Error: red border flash, error message in DM Mono

**Gallery strip (right):** Vertical stack of recent capture thumbnails, each with its top taxonomy label as caption. Clicking any navigates to Screen 2 (Result) for that capture.

**Header:** Minimal. `SAKKAD` left-aligned in Cormorant, small. Right: `GET /api/health` status dot (green/red). No nav beyond that.

---

### Screen 2: Result (Classification Breakdown)

This is the main showcase screen. Triggered after upload completes or when clicking a gallery capture.

**Layout:** Three-column asymmetric grid.

```
┌─────────────────┬────────────────────────┬───────────────────────┐
│  IMAGE          │  TAXONOMY              │  REFERENCES           │
│  + PALETTE      │  + LAYER TAGS          │  + EXPLANATION        │
│  (col 1, 35%)   │  (col 2, 35%)          │  (col 3, 30%)         │
└─────────────────┴────────────────────────┴───────────────────────┘
```

#### Column 1 — Image + Palette

- Full image (aspect-ratio preserved, max height 70vh)
- Below image: palette swatches extracted from `tags.palette` (5 hex circles, no labels, just color)
- Caption: upload timestamp in DM Mono, small

#### Column 2 — Taxonomy + Tags

**Taxonomy matches section:**

Label: `TAXONOMY` in small-caps DM Mono.

Each `taxonomy_matches` entry (top 5):

- Label name in Cormorant, medium weight
- Domain badge: `fashion_streetwear` | `abstract_visual` | `visual_context` in tiny DM Mono
- Score bar: horizontal bar fills left-to-right on mount, width = score × 100%, amber fill, 700ms ease-out, each bar delayed 80ms from previous
- Score number: right-aligned, DM Mono, 2 decimal places

**Layer 1 tags section:**

Label: `LAYER 1 — VISUAL FACTS` in small-caps DM Mono.

`layer1_tags` rendered as a flowing tag cloud. Single words, rounded pill shape, subtle border. No scores.

**Layer 2 tags section:**

Label: `LAYER 2 — FASHION DESCRIPTORS` in small-caps DM Mono.

`layer2_tags` rendered as hyphenated pills in a different color tint. If the `is_abstract` path was taken, show label: `LAYER 2 — MATERIAL LANGUAGE` instead of `LAYER 2 — FASHION DESCRIPTORS`. Detection: the `BackendCapture` response does not include a `domain` field, so infer from the top `taxonomy_matches` key — if it matches any known `abstract_visual` labels (e.g. "Concrete Brutalism", "Botanical Organic", "Oxidized Metal", "Cellular Pattern", etc.), treat as abstract. Maintain a local `ABSTRACT_VISUAL_LABELS` set in `types.ts` for this check.

#### Column 3 — References + Narrative

**Reference matches section:**

Label: `DESIGNER REFERENCES` in small-caps DM Mono.

Top 3 `reference_matches` entries (those with score > 0.15 shown in full; below 0.15 shown dimmed):

- Brand name in Cormorant, large
- Reference title in DM Mono, small
- Score as a percentage-style meter (same animated bar as taxonomy)
- Description text below, small DM Mono, muted

**Explanation section:**

`reference_explanation` displayed as a blockquote-style pull quote. Large Cormorant italic. This is the human-readable narrative — it should feel like editorial copy, not a data field.

**Reflection CTA** (if `session_id` is present):

A button: `GENERATE SESSION REFLECTION →` in DM Mono. Calls `GET /api/sessions/{id}/reflection`. Reflection text appears below in the same blockquote style, replacing the CTA.

---

### Pipeline Reveal (during upload processing)

While `POST /api/capture` is in flight, show a live stage tracker below the image preview in Screen 1. Stages appear sequentially with a typing-cursor animation:

```
✓ Image uploaded to storage
✓ SigLIP embedding computed
✓ Taxonomy classified
✓ Designer references matched
✓ Palette extracted
✓ Layer 1 tags generated (Gemini)
✓ Layer 2 tags generated (Gemini)
✓ Narrative explanation written
```

Each stage revealed on a 400ms timer after the previous, regardless of actual async order (the backend returns everything at once — this is a choreographed reveal for the demo effect).

When complete: auto-transition to Screen 2 with a slow cross-fade.

---

## Data Flow

```
App.tsx
  ├── useCapture() hook
  │     POST /api/capture (multipart)
  │     returns: BackendCapture + gemini_models
  │
  ├── useGallery() hook
  │     GET /api/gallery
  │     returns: BackendCapture[]
  │
  └── useReflection(sessionId) hook
        GET /api/sessions/{id}/reflection
        returns: { reflection, fallback_used, capture_count }
```

All API calls include `ngrok-skip-browser-warning: true` header (configurable via `VITE_API_BASE_URL` env var, defaults to `http://127.0.0.1:8000`).

---

## Tech Stack

```
React 19 + Vite + TypeScript
Tailwind v4 (for utility layout)
Framer Motion (for score bar animations, panel reveals, cross-fades)
Google Fonts: Cormorant Garamond + DM Mono
```

No Supabase client in this app — reads exclusively from the FastAPI backend, which handles Supabase internally.

---

## File Structure

```
sakad-backend/demo/
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── package.json
├── .env.example         # VITE_API_BASE_URL=http://127.0.0.1:8000
└── src/
    ├── main.tsx
    ├── App.tsx          # Router: / → UploadScreen, /capture/:id → ResultScreen
    ├── hooks/
    │   ├── useCapture.ts
    │   ├── useGallery.ts
    │   └── useReflection.ts
    ├── components/
    │   ├── UploadZone.tsx          # Drop zone + pipeline reveal
    │   ├── GalleryStrip.tsx        # Right-column recent captures
    │   ├── ResultLayout.tsx        # Three-column shell
    │   ├── ImagePanel.tsx          # Col 1: image + palette
    │   ├── TaxonomyPanel.tsx       # Col 2: taxonomy + tags
    │   ├── ReferencesPanel.tsx     # Col 3: references + explanation + reflection
    │   ├── ScoreBar.tsx            # Animated score bar (reused in both panels)
    │   ├── TagPill.tsx             # Reused for layer1 and layer2 tags
    │   └── PipelineReveal.tsx      # Stage-by-stage processing reveal
    ├── lib/
    │   ├── api.ts                  # All fetch calls, typed
    │   └── types.ts                # BackendCapture, ReflectionResponse
    └── styles/
        └── globals.css             # CSS custom properties, font imports, base reset
```

---

## Design Tokens (CSS custom properties)

```css
--color-bg: #0a0a0a;
--color-surface: #141414;
--color-border: #2a2a2a;
--color-accent: #c9a96e;
--color-text-primary: #f0ece4;
--color-text-muted: #6b6760;
--color-score-fill: #c9a96e;
--font-display: "Cormorant Garamond", serif;
--font-mono: "DM Mono", monospace;
```

---

## States Required (all components)

Every component must handle:

- **Loading:** skeleton loaders (dark surface, no shimmer — subtle pulse only)
- **Empty:** descriptive message + expected action, never blank
- **Error:** DM Mono error text, amber border, retry option
- **No session_id:** hide reflection CTA entirely (no disabled state — just absent)

---

## Accessibility

- WCAG AA contrast on all text against backgrounds
- `prefers-reduced-motion`: disable all Framer Motion animations, show final states immediately
- Keyboard: drop zone activatable via Enter/Space, all clickable elements focusable
- `alt` text on all images using top taxonomy label as fallback

---

## Anti-Slop Checklist

- [ ] No Inter, Roboto, Arial — using Cormorant + DM Mono only
- [ ] No purple gradients
- [ ] No card grid with identical rounded corners — asymmetric layout
- [ ] No generic hero centered-text block
- [ ] Score bars animate on mount — not static
- [ ] Pipeline reveal is choreographed — feels alive
- [ ] Taxonomy domain badges distinguish `fashion_streetwear` from `abstract_visual`
- [ ] Layer 2 label changes based on path (fashion vs abstract)
- [ ] reference_explanation rendered as editorial pull quote, not a data field
- [ ] All states handled (loading, error, empty, no session)

---

## One-Shot / Few-Shot Guidance for Claude 3.5 or o3

This spec is designed to be passed directly to a high-reasoning model. To maximize output quality:

**One-shot prompt structure:**

1. Paste this entire spec
2. Add: "Build the complete app. Start with `src/lib/types.ts` and `src/lib/api.ts`, then implement components in the order listed in File Structure. Use the exact design tokens defined. Implement all states."

**Few-shot prompt structure (recommended for complex reasoning models):**

- Shot 1: `src/lib/types.ts` + `src/lib/api.ts` — establish the data contract first
- Shot 2: `ScoreBar.tsx` + `TagPill.tsx` — nail the atomic components and animation
- Shot 3: `TaxonomyPanel.tsx` + `ReferencesPanel.tsx` — the data-heavy columns
- Shot 4: `UploadZone.tsx` + `PipelineReveal.tsx` — the interactive core
- Shot 5: `App.tsx` + `ResultLayout.tsx` + `GalleryStrip.tsx` — wire it all together

**High-reasoning vs regular model guidance:**

- Regular (Sonnet 3.5): provide the file structure and ask for one file at a time. It will follow instructions precisely but needs explicit prompting per file.
- High-reasoning (o3, o3-mini): pass the full spec + "implement the complete app" in one shot. It will infer component composition, state management, and animation choreography without being prompted per file. It handles ambiguity better and makes better aesthetic judgment calls without guardrails.

For the demo, **o3 one-shot is the recommended path**. The spec is comprehensive enough that a high-reasoning model can produce a working, styled, multi-screen app in a single generation.
