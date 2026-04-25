# Backend Showcase UI Design

## Purpose

Create a standalone browser UI that makes the Sakkad backend legible as a fashion-intelligence system: upload inspiration, run SigLIP classification, show Gemini layer tags, surface designer/reference influences, group images into a relationship set, and generate short backend-proxied narrative copy.

This is a demo/product surface with an expressive fashion shell and a product-grade analysis workflow.

## Design Mode

- **Primary mode:** Marketing / Expressive, because the UI must impress during a live demo and communicate taste.
- **Section override:** Product UI for upload, results, errors, and API status because users need clear state and scannable data.
- **Industry direction:** Fashion / Luxury Brand. Use restrained material depth, editorial typography, slow premium reveals, and high-quality image treatment.

## Constraints From Existing Code

- This repo has no existing React/Vite frontend.
- Backend endpoints already provide the needed data:
  - `POST /api/capture`
  - `GET /api/gallery`
  - `GET /api/captures/{id}`
  - `POST /api/generate`
  - `GET /api/health`
- The UI should not call Supabase directly for this showcase.
- The UI must not expose Gemini or Supabase service keys.
- `POST /api/capture` accepts one file per request; multi-image upload must queue sequential requests.
- `taxonomy_matches` is a score object and should be sorted descending in the UI.
- Optional enrichment fields may be `null`.
- Current checked-in taxonomy is 81 labels: 56 `fashion_streetwear` and 25 `abstract_visual`. The UI must treat garments, textures, surfaces, and environmental references as equal inspiration sources.
- The public demo path may use ngrok or Cloudflare Tunnel. API calls should include `ngrok-skip-browser-warning: true`, but the UI copy should not assume ngrok is always the tunnel.
- `/api/generate` returns one text item per request. To create multiple suggested relationship statements, call the existing endpoint for the supported kinds rather than inventing a fake batch endpoint.

## Product Flow To Mirror

From the partner UI recording, the important flow is:

1. A canvas-like captures view shows image thumbnails in loose circular groups.
2. The user opens an **Explore Relationships** panel for a selected group.
3. The panel has three conceptual columns:
   - **Suggested Relationships**
   - **Grouped Images**
   - **Tags & Taxonomy**
4. The taxonomy/tag column mixes aesthetic labels, designer references, and descriptive material attributes.
5. The user selects one generated relationship statement.
6. The interface transitions into a **Generating Sketch** stage.

The showcase should reproduce this product rhythm, not duplicate the partner repo or visual code.

## Visual Direction

### Working Name

**Sakkad Atelier**

### Aesthetic

Apple-adjacent material hierarchy with fashion editorial restraint:

- translucent porcelain panels over warm stone/champagne gradients
- soft glass borders and large-radius surfaces, but not generic glassmorphism
- image-first composition with one dominant capture on a raised plinth
- analytical data rendered like a studio contact sheet, not a SaaS dashboard
- black ink, warm ivory, champagne brass, muted moss/oxide accents
- circular grouping fields inspired by the partner canvas, treated like soft spotlight pools rather than literal copied shapes

### Typography

Use a distinctive but readable pairing:

- Display/editorial: `Instrument Serif` or `Playfair Display`
- UI/body: `Manrope`, `Source Sans 3`, or `DM Sans`

Avoid default system-only typography for the expressive layer. Small metadata and controls should still prioritize legibility.

### Motion

- Slow entrance choreography for hero, upload panel, and result cards.
- A tasteful "analysis pass" progress rail during upload/classification.
- Hover depth on capture cards and reference cards.
- No noisy particles or gimmick motion.
- All animation must respect `prefers-reduced-motion`.

### Responsive Layout

- Desktop: two-column stage.
  - Left: upload/image plinth and gallery strip.
  - Right: analysis stack with taxonomy, tags, references, explanation.
- Tablet: stacked image first, analysis second.
- Mobile: single-column, sticky bottom upload action, horizontally scrollable reference/taxonomy chips only where appropriate.

## Approaches Considered

### A. Standalone React/Vite Showcase App In `web/sakkad-showcase/`

Build a focused React + TypeScript app that calls the backend directly.

Pros:

- Best match for the user-provided frontend context and partner-facing handoff.
- Strong component boundaries for upload, analysis, gallery, and narrative generation.
- Straightforward testing with Vitest and React Testing Library.
- Can evolve into a deployable demo without changing backend routes.
- Keeps showcase separate from the backend internals and the missing partner app.

Cons:

- Adds Node/Vite tooling to a Python-only repo.
- Dependency install may require network approval.
- Requires separate dev command from the FastAPI server.

### B. FastAPI-Served Static Showcase Under `sakad-backend/static/`

Create a static HTML/CSS/JS page served by FastAPI.

Pros:

- Minimal tooling and no separate Node install.
- One backend process can serve both API and UI.
- Good fallback if dependency installation is blocked.

Cons:

- Harder to test behavior rigorously.
- Type safety and component reuse are weaker.
- More likely to become a one-off demo page rather than a maintainable surface.
- Less aligned with the React/Vite partner app context.

### C. Modify The Separate Partner Frontend

Use the `web/sakkad-app/` frontend described in the handoff.

Pros:

- Best if the goal is to update the production partner UI directly.
- Already has React, Vite, Supabase, Framer Motion, and app concepts.

Cons:

- That frontend is not present in this repo.
- The local task would require cross-repo work and likely private context.
- It would blur the distinction between a backend demo UI and the partner app.

## Recommendation

Choose **Approach A: standalone React/Vite showcase app in `web/sakkad-showcase/`**.

Reasoning:

- The user wants a working, high-quality UI, not just API docs.
- A focused React app can demonstrate upload/classification while preserving the separate partner frontend architecture.
- It keeps backend and frontend contracts explicit through a typed API client.
- It supports real tests and future deployment better than a static one-off page.

If Node dependency installation is blocked, fall back to Approach B only after confirming with the user.

## Proposed Information Architecture

### 1. Top Bar

- Sakkad wordmark
- Backend status pill from `GET /api/health`
- Backend URL indicator
- "API contract" secondary link or disclosure

### 2. Hero / Thesis

Short editorial positioning:

> "A visual research engine for fashion intuition."

Support copy explains: Spectacles capture inspiration, backend enriches it with SigLIP taxonomy, Gemini tags, and designer reference retrieval.

### 3. Upload Atelier

- Accessible drag-and-drop image area plus normal file picker.
- Optional session id field or auto-generated local session field.
- Multiple files accepted in UI, queued as individual `POST /api/capture` calls.
- Warmup copy: first run can take longer while SigLIP loads.

### 4. Relationship Canvas

Mirror the important flow from the partner UI without copying its code:

- canvas/contact-sheet view of classified captures
- capture cards arranged in soft circular groups
- user can select 2-4 captures into an active relationship group
- selected group opens an "Explore Relationships" panel

### 5. Explore Relationships Panel

Use the same conceptual three-column flow:

- **Suggested Relationships:** backend-generated relationship/creative statements derived from selected capture ids
- **Grouped Images:** selected capture thumbnails and their top labels
- **Tags & Taxonomy:** aggregated taxonomy labels, layer1 tags, layer2 tags, references, and material cues, including abstract labels such as `Patinated Finish`, `Concrete Brutalism`, `Muted Wash`, or `Botanical Organic`

### 6. Analysis Stage

For the active capture:

- Large image preview.
- Top taxonomy label and confidence.
- Ranked taxonomy bars for top 5.
- Layer 1 tags as simple visual descriptors.
- Layer 2 tags as fashion-specific hyphenated chips.
- Palette/tags when present.
- Reference explanation as the "description" block.
- Reference match cards with brand/title/score/description.
- Gemini model badges if returned by upload.

### 7. Gallery / Contact Sheet

- Load recent enriched captures from `GET /api/gallery`.
- Cards show image, top taxonomy label, top reference title, and created date.
- Selecting a card opens it in the same analysis stage.

### 8. Sketch Stage

- Show the selected relationship statement as the sketch prompt.
- Render a polished "Generate Sketch" stage that is disabled or marked "requires backend image endpoint" in MVP.
- Do not call Gemini image generation from the browser.

### 9. Narrative Drawer

- Select one or more captures.
- Call `POST /api/generate` with `kind: "creative_summary"` or `kind: "styling_direction"`.
- Render returned text with a fallback badge when `fallback_used` is true.

## Data Flow

```txt
App load
  -> GET /api/health
  -> GET /api/gallery
  -> render gallery or empty state

User uploads image(s)
  -> validate image file(s)
  -> POST /api/capture per file
  -> append returned capture to local captures
  -> set latest capture as active

User selects captures for relationship group
  -> POST /api/generate with capture_ids and kind=creative_summary
  -> POST /api/generate with capture_ids and kind=styling_direction
  -> POST /api/generate with capture_ids and kind=inspiration_prompt
  -> render relationship statements
  -> user selects one statement
  -> sketch stage displays selected statement and explains secure backend endpoint requirement
```

## Component Plan

- `App`: owns active capture, gallery, upload queue, and narrative selection.
- `api/client.ts`: typed backend client and error normalization.
- `components/UploadAtelier.tsx`: drag/drop and file picker.
- `components/RelationshipCanvas.tsx`: grouped/contact-sheet capture selection.
- `components/RelationshipPanel.tsx`: suggested relationships, grouped images, tags/taxonomy.
- `components/AnalysisStage.tsx`: active capture detail.
- `components/TaxonomyMeter.tsx`: sorted score visualization.
- `components/TagConstellation.tsx`: layer1/layer2 tags.
- `components/ReferenceRunway.tsx`: designer/reference cards.
- `components/GalleryContactSheet.tsx`: recent captures.
- `components/SketchStage.tsx`: selected statement and backend-image-generation placeholder.
- `components/StatusPill.tsx`: backend health.

## Relationship Statement Strategy

The current backend does not have a dedicated "five relationship statements" endpoint. Use the existing backend safely:

- Request `creative_summary`, `styling_direction`, and `inspiration_prompt` for the same selected capture ids.
- Render each successful response as a suggested relationship card.
- If a response has `fallback_used: true`, badge it as fallback rather than hiding that fact.
- If generation fails, build a local non-AI fallback from top taxonomy labels, layer2 tags, and reference titles so the panel remains useful.
- Do not call Gemini directly from the browser.

## Tags & Taxonomy Aggregation

For selected grouped captures:

- take top taxonomy labels across all selected captures, sorted by max score then frequency
- include `layer1_tags` as visual/material descriptors
- include `layer2_tags` as fashion/detail descriptors
- include top reference titles when `score >= 0.15`; below that threshold, de-emphasize as weak/noisy reference matches
- surface abstract/environmental labels alongside fashion labels because the product is about inspiration, not only outfit classification

## E2E Use Cases

### Use Case 1: Live Upload

- **Intent:** Demonstrate backend classification live.
- **Steps:** Start backend, open UI, upload `sakad-backend/test-images/western.jpg`, wait for result.
- **Verification:** Active result shows image, taxonomy scores, layer tags when available, references when available, and no secret values.
- **Persistence:** Capture row appears in Supabase via backend insert.

### Use Case 2: Gallery Fallback

- **Intent:** Keep demo useful if live upload is slow.
- **Steps:** Open UI against backend with seeded captures.
- **Verification:** Gallery cards render. Selecting a card shows the same analysis layout.
- **Persistence:** None beyond existing backend data.

### Use Case 3: Backend Unavailable

- **Intent:** Avoid a dead blank screen during setup problems.
- **Steps:** Open UI with an invalid `VITE_BACKEND_URL`.
- **Verification:** Health pill shows unavailable, gallery error is visible, upload is disabled or retryable with clear copy.
- **Persistence:** None.

### Use Case 4: Narrative Generation

- **Intent:** Show backend-proxied Gemini text safely.
- **Steps:** Select one or more captures, request creative summary.
- **Verification:** Text appears, source capture ids are preserved in response state, fallback badge appears when returned.
- **Persistence:** None.

### Use Case 5: Relationship-To-Sketch Flow

- **Intent:** Match the core product flow from the partner UI recording.
- **Steps:** Select 2-4 classified captures, open Explore Relationships, generate suggested statements, select one statement, view sketch stage.
- **Verification:** Relationship panel has Suggested Relationships, Grouped Images, and Tags & Taxonomy columns; sketch action is visible but secure-backend-gated.
- **Persistence:** None in MVP.

## Risks And Mitigations

- **Risk:** Adding Node tooling slows the session.
  - **Mitigation:** Scaffold minimal Vite app and keep dependencies small.
- **Risk:** First SigLIP inference appears hung.
  - **Mitigation:** Clear warmup state and progress copy.
- **Risk:** Optional backend fields are missing.
  - **Mitigation:** Null-safe rendering for every enrichment section.
- **Risk:** UI looks generic.
  - **Mitigation:** Use image-first editorial composition, custom tokens, distinctive type, and constrained luxury palette.
- **Risk:** Secrets leak through frontend env.
  - **Mitigation:** Only allow `VITE_BACKEND_URL`; no Gemini or Supabase keys in frontend docs.
- **Risk:** Users expect sketch generation to work because the partner UI does it.
  - **Mitigation:** Show the sketch stage but label the action as requiring a backend-proxied image endpoint before enabling it.

## Acceptance Check Before Implementation

- [ ] User approves standalone app path or chooses FastAPI static fallback.
- [ ] User approves MVP order: single upload first, gallery second, batch/narrative after.
- [ ] TDD implementation plan is written and reviewed.
