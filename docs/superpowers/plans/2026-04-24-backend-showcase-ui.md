# Backend Showcase UI Implementation Plan

## Goal

Build `web/sakkad-showcase/`, a standalone React/Vite/TypeScript UI that demonstrates the Sakkad backend while matching the partner app's important flow: upload image(s), classify through `POST /api/capture`, arrange captures on a canvas/contact sheet, select a group, open an Explore Relationships panel, render SigLIP taxonomy, layer1/layer2 tags, designer references, generated relationship statements, and a secure-backend-gated sketch stage.

## Recommended Stack

- React + TypeScript + Vite
- Tailwind v4 via `@tailwindcss/vite` if dependencies can be installed cleanly
- Vitest + React Testing Library for component/API tests
- No Supabase JS client
- No client Gemini key

## Files To Create

- `web/sakkad-showcase/package.json`
- `web/sakkad-showcase/index.html`
- `web/sakkad-showcase/vite.config.ts`
- `web/sakkad-showcase/tsconfig.json`
- `web/sakkad-showcase/src/main.tsx`
- `web/sakkad-showcase/src/App.tsx`
- `web/sakkad-showcase/src/index.css`
- `web/sakkad-showcase/src/types.ts`
- `web/sakkad-showcase/src/lib/api.ts`
- `web/sakkad-showcase/src/lib/format.ts`
- `web/sakkad-showcase/src/components/AnalysisStage.tsx`
- `web/sakkad-showcase/src/components/RelationshipCanvas.tsx`
- `web/sakkad-showcase/src/components/RelationshipPanel.tsx`
- `web/sakkad-showcase/src/components/SketchStage.tsx`
- `web/sakkad-showcase/src/components/StatusPill.tsx`
- `web/sakkad-showcase/src/components/UploadAtelier.tsx`
- `web/sakkad-showcase/src/test/*.test.tsx`
- `web/sakkad-showcase/src/test/fixtures.ts`
- `web/sakkad-showcase/.env.example`
- `web/sakkad-showcase/README.md`

## Implementation Principles

- Write a failing test before each production behavior.
- Keep API calls in `src/lib/api.ts`; components receive typed data and callbacks.
- Render null/missing optional fields intentionally.
- Sort taxonomy scores client-side by score descending.
- Aggregate selected-group taxonomy/tags across both `fashion_streetwear` and `abstract_visual`; do not assume every capture is a garment.
- Keep backend URL configurable via `VITE_BACKEND_URL`, defaulting to `http://127.0.0.1:8000`.
- Add `ngrok-skip-browser-warning: true` header to API calls because demo/live may use ngrok.
- Do not include any Gemini/Supabase secret in frontend code or env examples.
- Mirror the partner app's relationship flow without copying its code: canvas grouping, Explore Relationships panel, Suggested Relationships, Grouped Images, Tags & Taxonomy, selected prompt, sketch stage.

## Phase 0: Scaffold Tooling

This phase creates the minimum test/build harness. It should not implement product behavior yet.

1. Create `web/sakkad-showcase/` package and config files.
2. Add dependencies/scripts:
   - `dev`: Vite dev server
   - `build`: TypeScript check plus Vite build
   - `test`: Vitest
   - `lint`: ESLint if included, otherwise TypeScript build is the minimum frontend static check
3. Add `.env.example` with only:

```txt
VITE_BACKEND_URL=http://127.0.0.1:8000
```

4. Verify `npm install` or `pnpm install` availability. If dependency install fails because of network/sandboxing, request approval before retrying.

Checkpoint:

- [ ] `npm test` runs and reports no tests yet or one placeholder test.
- [ ] `npm run build` reaches the expected initial state after minimal entrypoint exists.

## Phase 1: Typed API Client

### RED

Create tests for `src/lib/api.ts`:

- `getGallery()` calls `${baseUrl}/api/gallery`, includes `ngrok-skip-browser-warning`, and returns captures.
- `uploadCapture()` sends `FormData` to `/api/capture` and does not set a manual `Content-Type`.
- `generateCopy()` sends `{ kind, capture_ids }` to `/api/generate`.
- failed JSON response becomes a readable `ApiError`.

Run:

```bash
cd web/sakkad-showcase
npm test -- src/test/api.test.ts
```

Expected: fail because client does not exist.

### GREEN

Implement:

- `BackendCapture`, `ReferenceMatch`, `GenerateResponse`, `HealthResponse` types.
- `getBackendBaseUrl()`.
- `apiFetch()` helper with error normalization.
- `getHealth()`, `getGallery()`, `uploadCapture()`, `generateCopy()`.

### REFACTOR

- Centralize headers.
- Keep `FormData` upload path separate so browser sets multipart boundary.
- Add small helpers for sorting taxonomy.

Checkpoint:

- [ ] API tests pass.

## Phase 2: Capture Formatting Helpers

### RED

Create tests for `src/lib/format.ts`:

- taxonomy entries sort descending.
- top taxonomy label returns `null` for empty object.
- reference score formatting handles `null`.
- created date formatting handles invalid/missing dates gracefully.
- selected capture aggregation includes taxonomy, layer1 tags, layer2 tags, and meaningful reference titles.
- abstract labels like `Patinated Finish` and `Concrete Brutalism` are preserved rather than filtered out.

Expected: fail because helpers do not exist.

### GREEN

Implement only the helpers needed by components.

### REFACTOR

Remove repeated formatting logic from tests and prepare fixtures.

Checkpoint:

- [ ] Formatting tests pass.

## Phase 3: Analysis Stage Components

### RED

Create component tests using fixture captures:

- `AnalysisStage` renders image alt text, top taxonomy, layer1 tags, layer2 tags, reference explanation, and reference cards.
- Missing `reference_matches`, tags, or taxonomy renders intentional empty state copy.
- `TaxonomyMeter` displays top 5 sorted scores.

Expected: fail because components do not exist.

### GREEN

Implement:

- `AnalysisStage`
- `TaxonomyMeter`
- `TagConstellation`
- `ReferenceRunway`
- selected-group aggregation helpers if not already implemented in `format.ts`

Use semantic sections and accessible labels.

### REFACTOR

- Extract common empty-state component only if repeated.
- Keep visual styling tokens in CSS, not duplicated across components.

Checkpoint:

- [ ] Analysis component tests pass.

## Phase 4: Upload Atelier

### RED

Create component tests:

- file input has label and accepts image files.
- selecting a file shows preview/name.
- submit calls provided `onUpload(files)` callback.
- disabled/loading state prevents duplicate submit.
- non-image file displays validation error.

Expected: fail because component does not exist.

### GREEN

Implement:

- drag/drop wrapper
- standard file input fallback
- file preview list
- warmup/loading copy
- accessible button states

### REFACTOR

- Keep browser object URL cleanup in `useEffect`.
- Avoid custom drag/drop behavior that breaks keyboard access.

Checkpoint:

- [ ] Upload tests pass.

## Phase 5: App Integration

### RED

Create integration-style component tests for `App` with mocked API client:

- app loads gallery and selects first capture when available.
- upload success prepends returned capture and makes it active.
- upload failure displays an error but keeps existing gallery visible.
- health failure displays unavailable status.

Expected: fail because `App` is not wired.

### GREEN

Wire:

- initial `getHealth()` and `getGallery()`
- upload queue, one `POST /api/capture` per file
- active capture selection
- gallery contact sheet
- top-level status and error handling

### REFACTOR

- Keep state minimal and explicit.
- Extract `GalleryContactSheet` and `StatusPill` if `App` becomes too dense.

Checkpoint:

- [ ] App integration tests pass.

## Phase 6: Relationship Panel And Sketch Stage

### RED

Create tests:

- selecting multiple captures opens an Explore Relationships panel.
- selected capture ids are sent to `generateCopy()` for `creative_summary`, `styling_direction`, and `inspiration_prompt`.
- returned relationship text renders in Suggested Relationships.
- `fallback_used: true` renders a fallback badge on that statement.
- failed generation still renders a local deterministic relationship statement from taxonomy/tags.
- Grouped Images column shows selected thumbnails.
- Tags & Taxonomy column aggregates selected capture labels/tags.
- selecting a relationship statement updates the sketch prompt.
- sketch action is visible but disabled with "requires backend image endpoint" copy.
- no selection disables relationship generation.

Expected: fail because relationship UI does not exist.

### GREEN

Implement:

- capture selection in gallery/results
- `RelationshipCanvas`
- `RelationshipPanel`
- `SketchStage`
- generation orchestration for the three existing backend `kind` values
- local deterministic fallback statement builder

### REFACTOR

- Keep this feature secondary in the layout so it does not compete with classification.
- Keep sketch-generation state explicit and do not fake a successful generated image.
- Keep relationship generation resilient: one failed statement should not blank the whole panel.

Checkpoint:

- [ ] Relationship/sketch tests pass.

## Phase 7: Visual System And Polish

### RED

Add lightweight tests/checks where practical:

- primary landmarks exist: `header`, `main`, named sections.
- upload and generate controls are reachable by accessible names.

Expected: fail if semantics are incomplete.

### GREEN

Implement final CSS:

- CSS variables for color, spacing, type, radii, shadows, motion.
- luxury monochrome/champagne palette.
- responsive desktop/tablet/mobile layout.
- `prefers-reduced-motion` overrides.
- focus-visible states.
- empty/loading/error states.

### REFACTOR

- Remove unused classes and visual dead code.
- Confirm no generic placeholder rectangles remain.

Checkpoint:

- [ ] Semantic/accessibility tests pass.
- [ ] Visual UI is ready for manual review.

## Phase 8: Manual E2E Smoke

Use real backend where credentials are configured.

1. Start backend:

```bash
cd sakad-backend
uvicorn main:app --reload
```

2. Start UI:

```bash
cd web/sakkad-showcase
npm run dev
```

3. Upload one real image:

```txt
sakad-backend/test-images/western.jpg
```

4. Verify:

- health pill shows backend availability
- upload transitions through loading to result
- image appears
- taxonomy scores render
- layer1/layer2 tag sections render or show intentional unavailable copy
- abstract/environmental labels render when testing `tree_bark.jpg`, `concrete_wall.jpg`, `rusted_pipes.jpg`, or `leaf.jpg`
- references render or show intentional unavailable copy
- explanation renders when present
- gallery remains usable

5. Optional:

- select one or more captures
- open Explore Relationships
- request relationship statements
- select one statement
- verify sketch stage shows secure-backend-gated action

Checkpoint:

- [ ] E2E use cases tested and notes recorded.

## Phase 9: Quality Gates

Run from frontend app:

```bash
cd web/sakkad-showcase
npm test
npm run build
```

Run backend suite to verify no backend regression:

```bash
cd sakad-backend
python -m pytest && ruff check . && mypy --strict .
```

Known repository blocker from `CONTINUITY.md`: `ruff` and `mypy` may be missing in the current shell. If still missing, record the exact failure and do not claim the full verify gate passed.

## Plan Review

### P0/P1/P2 Findings

- None.

### Non-Blocking Risks

- Dependency installation may be blocked by network restrictions. Mitigation is explicit approval request and a fallback static implementation if needed.
- Tailwind v4 setup adds dependency weight. Mitigation is to keep styling in `index.css` with design tokens and use Tailwind only if setup is smooth.
- Batch upload could expand state complexity. Mitigation is to implement single-file upload first, then queue multiple files after tests pass.

### Recommendation After Review

Proceed with Approach A, but implement in this order:

1. Scaffold minimal Vite test harness.
2. Build typed API client.
3. Build single-upload analysis flow.
4. Add gallery.
5. Add relationship panel and sketch-stage placeholder only after the core path is green.
