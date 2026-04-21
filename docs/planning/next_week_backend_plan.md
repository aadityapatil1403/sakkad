# Next Week Backend Plan

## Summary
The next week should focus on one primary outcome: **a live session produces captures that return strong image-first taxonomy, curated designer/reference matches, and short explanations per capture**. Do **not** spend this week on Pipeline B rollout, `layer3` production use, or full relationship-panel generation. The current backend already supports capture/session ingestion and image-first taxonomy, so the best use of time is to add the missing retrieval layer and shape the APIs the web app will need next.

Chosen direction:
- **Primary focus:** Retrieval-first backend
- **Demo target by end of week:** `Capture + References`
- **Parallelization:** Yes, optimized for multiple Codex worktrees
- **Corpus strategy:** Small curated seed
- **Relationship endpoint:** Wait until Week 2

## Goal State By End of Week
A single capture flow should produce:
- stored image + session linkage
- `taxonomy_matches`
- palette
- optional `layer1_tags` / `layer2_tags` when Gemini succeeds
- `reference_matches`
- `reference_explanation`

A session flow should support:
- start session
- end session
- list sessions
- session detail or gallery payloads that include reference-enriched captures

This week’s success criteria:
- a live session on Spectacles or a backend smoke run can create captures with reference retrieval
- the web app can fetch sessions/captures and render designer/reference matches
- if Gemini fails, capture still succeeds and retrieval/taxonomy still work
- all of this is demoable without hybrid taxonomy or relationship statements

## Workstreams
### Workstream 1 — Reference Corpus and Retrieval
Build the new retrieval backbone on top of the current SigLIP image-first system.

Key changes:
- Define a small curated reference corpus schema for the MVP:
  - designer
  - brand/house
  - collection/era
  - short description
  - optional reference image URL
  - optional taxonomy/style tags
  - embedding
- Decide the storage location for MVP:
  - use Supabase as the source of truth for the corpus and embeddings
- Add seeding support for the small curated corpus
- Add retrieval logic:
  - `image_vec -> top reference matches`
- Ensure retrieval returns ranked reference objects suitable for API output

Deliverable:
- a seeded, queryable reference corpus with nearest-neighbor retrieval from capture embeddings

Recommended ownership:
- one parallel agent owns schema + seed path
- one parallel agent owns retrieval service logic + tests

### Workstream 2 — Capture Route Enrichment
Extend the current capture pipeline without changing the core image-first classifier.

Key changes:
- Keep current pipeline:
  - image upload
  - image embedding
  - taxonomy match
  - palette
  - optional `layer1` / `layer2`
- Add retrieval after `image_vec` is available:
  - call retrieval service
  - attach `reference_matches`
- Add a short explanation layer:
  - use taxonomy + reference matches + optional tags
  - generate a concise `reference_explanation`
- Keep all LLM outputs best-effort
- Preserve current fallback behavior:
  - if Gemini fails, capture still returns taxonomy + references

Deliverable:
- `POST /api/capture` returns designer/reference matches and explanation in addition to current fields

Recommended ownership:
- one parallel agent owns response shape + route integration
- one parallel agent owns explanation helper + failure/fallback behavior

### Workstream 3 — Session and Read APIs for the Web App
Shape the data the web app actually needs for the end-of-week demo.

Key changes:
- Review current `GET /api/sessions` and `GET /api/gallery`
- Add a session detail read API if needed:
  - `GET /api/sessions/{id}`
- Ensure read payloads include enriched capture data:
  - taxonomy
  - palette
  - optional tags
  - reference matches
  - reference explanation
- Keep the response shaped for:
  - session folders
  - session album views
  - capture metadata rendering in the web app

Deliverable:
- a clean web-app-facing read path for session + capture exploration

Recommended ownership:
- one parallel agent owns session detail/read route design and implementation

### Workstream 4 — Reliability, Observability, and Smoke Validation
Protect the current working system while adding retrieval.

Key changes:
- Add lightweight logging/observability for:
  - capture success/failure
  - Gemini failure rate
  - retrieval empty-hit rate
- Add smoke coverage for:
  - capture still succeeds when Gemini fails
  - retrieval returns sane results
  - session endpoints still work
- Keep taxonomy cache behavior unchanged and documented

Deliverable:
- confidence that the new retrieval layer does not destabilize capture/session flows

Recommended ownership:
- one parallel agent owns tests + smoke validation + logging additions

## Sequential Execution Order
Even with parallel worktrees, the integration order should be:

1. **Lock corpus schema and seed format**
   - this is the dependency for retrieval and read responses

2. **Implement retrieval service**
   - can proceed once schema is locked

3. **Wire retrieval into `/api/capture`**
   - depends on retrieval service

4. **Add explanation field**
   - depends on capture having retrieval results

5. **Add session detail/read API updates**
   - depends on enriched capture shape being stable

6. **Run full smoke validation**
   - only after all above are integrated

## Parallel Agent Handoffs
### Agent A — Corpus + Seed
Task:
- define the MVP reference corpus schema and Supabase storage plan
- add a seed script for a small curated dataset
- ensure embeddings are stored and retrievable

Done when:
- the corpus can be seeded reproducibly
- there is a small high-quality dataset ready for demo retrieval

Constraints:
- keep the corpus intentionally small and curated
- do not overbuild a large ingestion pipeline

### Agent B — Retrieval Service
Task:
- build retrieval from `image_vec` to ranked references
- expose a simple service interface used by routes
- add tests for ranking and empty-corpus behavior

Done when:
- given an embedding, the service returns top matches in a stable shape

Constraints:
- use the existing SigLIP-centered architecture
- do not introduce agentic orchestration or hybrid taxonomy work

### Agent C — Capture Route Enrichment
Task:
- integrate retrieval into `/api/capture`
- add `reference_matches`
- add `reference_explanation`
- preserve Gemini best-effort fallback behavior

Done when:
- `/api/capture` returns enriched results without regressing current taxonomy behavior

Constraints:
- do not touch the production classifier logic beyond reading the existing image embedding

### Agent D — Session/Web Read APIs
Task:
- add or refine `GET /api/sessions/{id}` and related read responses
- ensure session/capture payloads are shaped for the web app demo

Done when:
- the web app can fetch an enriched session payload without extra joins in the frontend

Constraints:
- keep response shapes simple and front-end friendly
- no relationship endpoint this week

### Agent E — Validation and Observability
Task:
- add tests for capture fallback, retrieval shape, and read APIs
- add smoke-path logging/metrics where useful
- verify end-to-end demo paths

Done when:
- the backend can be trusted for a demo even with intermittent Gemini failures

Constraints:
- do not broaden scope into relationship generation or preference modeling

## Public Interfaces
This week’s intended API additions:
- `POST /api/capture`
  - add:
    - `reference_matches`
    - `reference_explanation`
- `GET /api/sessions/{id}` if missing
  - include enriched capture payloads
- keep existing session endpoints unchanged in purpose

Suggested reference match shape:
- id
- designer
- brand
- collection_or_era
- title or label
- score
- optional image_url
- short description

Suggested explanation field:
- one short paragraph or 2–3 sentences explaining why the reference matches this capture

## Test Plan
Must pass before the week’s work is considered done:
- capture route still succeeds when Gemini fails
- capture route returns taxonomy + palette + reference matches
- retrieval returns ranked results from seeded corpus
- empty or missing corpus fails safely
- session list still works
- session detail returns enriched captures
- smoke test over several images verifies:
  - taxonomy present
  - reference matches present for most images
  - no regression in current capture flow

## Assumptions
- The MVP’s primary user is a fashion designer, not a general inspiration collector
- Retrieval + explanation is the highest-value backend gap this week
- A small curated corpus is enough for the next demo
- Relationship-panel generation is more valuable after retrieval is solid, not before
- The current image-first SigLIP classifier remains production truth for this week
