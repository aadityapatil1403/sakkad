# Sakkad MVP Plan

## Summary
The 2-week MVP should optimize for one thing: turning captured fashion references into useful designer-facing insight. The fastest path is to keep the current image-first SigLIP classification pipeline, add curated designer/reference retrieval, and use an LLM only for explanation and reflection. Do not spend the MVP window trying to ship a full semantic Pipeline B, full agent system, or long-term taste graph.

Core MVP loop:
1. capture images in a session
2. classify each image with image-first taxonomy
3. retrieve nearest designer / collection / reference matches
4. generate concise explanations and group insights
5. present results in the web app so a designer can organize, compare, and reflect

## MVP Scope
### Must ship
- Spectacles capture flow:
  - start session
  - capture images
  - end session
  - persist session and capture records
- Capture enrichment:
  - SigLIP image embedding
  - fashion-only taxonomy matches
  - palette extraction
  - optional Gemini `layer1` / `layer2` tags when available
- Web app support:
  - list sessions
  - view session captures
  - view per-capture taxonomy, retrieved references, and explanation
  - support grouped-image relationship panel using backend generation
- Reference intelligence:
  - curated designer / collection / reference corpus
  - nearest-neighbor retrieval from `image_vec`
  - explanation layer that says why the references fit
- Reliability:
  - image-only taxonomy remains the production fallback
  - if Gemini fails, capture still succeeds

### Nice to have
- session summary text
- display `layer1` / `layer2` in UI when available
- lightweight relationship-panel generation for selected image groups
- basic save / pin / board metadata if frontend is ready

### Explicitly out of scope
- production rollout of Pipeline B hybrid taxonomy
- `layer3` / `layer4` in production
- full taste-memory system across many sessions
- full agentic orchestration
- deep personalization / preference learning
- perfect educational reasoning across all grouping modes
- image generation chaining as a dependency for MVP success

## Recommended Architecture
### Visual backbone
- Keep SigLIP as the core visual system.
- Use SigLIP image embeddings for:
  - taxonomy matching
  - nearest designer/reference retrieval
  - future clustering support

### Semantic layer
- Keep Gemini as an optional interpretation layer, not the core classifier.
- Use Gemini for:
  - `layer1`
  - `layer2`
  - short explanations
  - relationship-panel text
- If Gemini is unavailable, the product still works through image-first retrieval and classification.

### Retrieval-first intelligence
- Build a curated fashion reference corpus with:
  - designer name
  - brand / house
  - collection or era
  - short text description
  - optional canonical reference images
  - taxonomy / style tags
- Embed this corpus into the same retrieval system.
- For each capture, retrieve:
  - top reference designers
  - top collections / looks
  - top similar archived references

### Explanation layer
- Feed taxonomy + retrieved references + optional Gemini tags into the LLM.
- Generate:
  - “why this image fits these references”
  - relationship statements for grouped images
  - short session-level reflections later if time permits

## 2-Week Delivery Plan
### Week 1
- Stabilize current backend:
  - keep image-only taxonomy as production mode
  - confirm sessions + captures are reliable
  - confirm taxonomy cache behavior is correct
- Define and load the reference corpus:
  - seed initial curated designers / collections / references
  - store embeddings for retrieval
- Implement retrieval:
  - `image_vec -> top designer/reference matches`
- Add backend response support:
  - include retrieved references and short explanation fields in capture/session outputs
- Keep Gemini optional:
  - do not block capture on tag generation

### Week 2
- Add relationship-panel backend support:
  - accept grouped images or selected capture ids
  - generate 3–5 explanation statements using retrieved context
- Add session-level browsing support for the web app:
  - session detail response shaped for canvas / grouping / metadata rendering
- Add basic observability:
  - capture success rate
  - Gemini failure rate
  - retrieval hit sanity checks
- Run end-to-end demo validation:
  - live session capture
  - session appears in web app
  - references and explanations render correctly
  - fallback behavior works when Gemini fails

## Backend Responsibilities
### What the backend should own for MVP
- session lifecycle
- capture ingestion
- image storage + metadata persistence
- image embedding
- taxonomy classification
- designer/reference retrieval
- explanation generation
- grouped-image relationship generation
- API responses shaped for the web app and Spectacles client

### What the backend should not own yet
- frontend canvas manipulation logic
- inferred organization on behalf of the user
- heavy personalization logic
- autonomous agent workflows
- generation chaining orchestration

## APIs / Data Changes
### Existing APIs to keep
- `POST /api/capture`
- `POST /api/sessions/start`
- `POST /api/sessions/{id}/end`
- `GET /api/sessions`

### Additions recommended for MVP
- capture/session responses include:
  - `taxonomy_matches`
  - `palette`
  - optional `layer1_tags`
  - optional `layer2_tags`
  - `reference_matches`
  - `reference_explanation`
- new endpoint for grouped relationship statements, e.g.:
  - `POST /api/relationships`
- optional session detail endpoint if current gallery route is insufficient:
  - `GET /api/sessions/{id}`

## Acceptance Criteria
- A live Spectacles capture session can be started, used, and ended successfully.
- New session data appears in the web app.
- Every capture returns taxonomy and palette.
- Most captures return designer/reference retrieval results.
- If Gemini fails, capture still succeeds and retrieval/taxonomy still work.
- Grouped-image relationship statements can be generated for the web app demo.
- The system is demoable end-to-end without relying on experimental hybrid taxonomy.

## Assumptions
- Fashion designers are the primary user for the MVP.
- Image-first classification is good enough to ship.
- Retrieval + explanation is more valuable for MVP than deeper semantic re-architecture.
- A curated but relatively small designer/reference corpus is acceptable for the first demo.
