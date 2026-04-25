# PRD Discussion: Backend Showcase UI

**Status:** Complete
**Started:** 2026-04-24
**Participants:** User, Codex

## Original User Story

Create a sleek Apple-like, fashion-aware UI that explains and demonstrates the backend we just built. The UI should let someone upload one or more images, classify them through the backend, show a description, surface designer influences/references, and display layer 1 tags, layer 2 tags, and SigLIP taxonomy classification.

## Research Log

- Local backend contract: `sakad-backend/API_CONTRACT.md` documents `POST /api/capture`, `GET /api/gallery`, `GET /api/captures/{id}`, `GET /api/sessions`, `GET /api/sessions/{id}/reflection`, and `POST /api/generate`.
- User-provided frontend handoff: the partner React app is separate from Lens Studio and integrates through Supabase. This repo currently does not contain that `web/sakkad-app/` frontend.
- Apple Human Interface Guidelines: use hierarchy, harmony, consistency, material depth, clear affordances, and adaptive layout as inspiration, without copying Apple assets.
- React docs: form uploads should use semantic forms, named inputs, labels, and `FormData` submission.
- Vite docs: only `VITE_*` values are exposed client-side, and they must not contain secrets.
- Tailwind v4 docs: if Tailwind is used, prefer the Vite plugin and CSS-first setup.

## Refined Understanding

### Personas

- **Demo presenter:** Needs a polished screen that can explain the backend in under three minutes during a live demo.
- **Fashion student/designer:** Uploads inspiration images and wants to understand the visual language, taxonomy, and designer references.
- **Partner/frontend engineer:** Needs to see the backend payload shape and how to render it without exposing Gemini keys.

### User Stories

- **US-001: Upload and classify one image.** As a demo presenter, I want to upload a fashion or visual inspiration image and see backend classification results, so I can prove the SigLIP pipeline works end to end.
- **US-002: Upload a small batch.** As a student/designer, I want to drop multiple images and let them classify sequentially, so I can compare references and tags across inspiration.
- **US-003: Inspect a capture.** As a partner/frontend engineer, I want to see taxonomy scores, layer 1 tags, layer 2 tags, palette/tags, reference matches, and explanation in one consistent layout, so I can understand the data contract quickly.
- **US-004: Generate a short readout.** As a presenter, I want to select classified captures and request backend-generated summary copy, so the UI can show the narrative layer without any client-side Gemini key.
- **US-005: Browse existing gallery.** As a presenter, I want the page to load existing enriched captures from `GET /api/gallery`, so the demo still has useful content if live upload is slow.

### MVP Scope

- Scaffold a small standalone frontend in this repo because the partner app is not present locally.
- Use backend APIs directly, not Supabase direct reads, for the demo showcase.
- Support one or more image uploads by queuing individual `POST /api/capture` requests.
- Render the normalized backend capture shape from upload response or `GET /api/gallery`.
- Render clear loading, success, empty, and error states.
- Include responsive, accessible, fashion-luxury visual design with Apple-inspired depth/material cues.

### Non-Goals

- No Lens Studio bridge.
- No Supabase Realtime subscription in this showcase UI.
- No client-side Gemini API key.
- No Gemini image generation.
- No new database tables or schema changes.
- No backend clustering UI until `POST /api/clusters/run` and `GET /api/clusters` exist.
- No production authentication.

### Key Decisions

- Build this as a backend showcase/demo UI, not as a replacement for the partner web app.
- Prefer `POST /api/capture` and `GET /api/gallery` over direct Supabase access so the UI demonstrates the backend capabilities.
- Treat `reference_explanation` as the primary capture-level description. Use `POST /api/generate` only for selected capture/session narrative copy.
- The frontend must expose only a backend base URL, for example `VITE_BACKEND_URL`. No service keys or Gemini keys.

### Remaining Open Questions

- Should the showcase live under `web/sakkad-showcase/` or another path?
- Should the first implementation use Tailwind v4 or custom CSS modules/plain CSS to minimize setup risk?
- Should multiple upload be MVP or a fast-follow after the single-image flow is solid?
