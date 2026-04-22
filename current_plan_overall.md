# Current Plan Overall

## Snapshot
Sakkad backend is no longer in the "prove retrieval" phase. The current stack already supports:
- `POST /api/capture` with image upload, image embedding, taxonomy matches, palette extraction, Gemini layer1/layer2 tags, reference retrieval, and best-effort reference explanation
- session lifecycle endpoints: `POST /api/sessions/start`, `POST /api/sessions/{id}/end`, `GET /api/sessions`
- session detail read path: `GET /api/sessions/{id}`
- basic health endpoints and a seeded reference corpus path

The plan now needs to shift from "add retrieval" to **demo-readiness, partner handoff, and productionizing the demo path**.

## Primary Goal
By the live demo window, the backend should let Spectacles captures flow into a clean partner-facing API that supports:
- session creation and browsing
- capture-level inspection
- meaningful taxonomy and reference outputs
- cluster/group views over a session corpus
- lightweight Gemini-generated summaries or prompts where they add value
- deployment, observability, and fallback behavior that hold up during a demo

## Planning Principles
- Keep image-first classification as the production backbone
- Treat Gemini features as additive and best-effort
- Prefer stable read contracts over adding many experimental write paths
- Optimize for demo reliability before sophistication
- Seed enough high-quality demo data to make clusters and references believable

## Current Truth vs. Stale Plan
The older planning docs assumed these were still missing:
- reference corpus and retrieval
- capture enrichment with references
- session detail API

Those are already present in the backend. The next plan should therefore focus on the gaps that remain between the current implementation and a partner-ready demo.

## Workstreams

### 1. API Contract and Read Surface Hardening
Goal: make the backend easy for the partner web app to consume without one-off interpretation.

Key outputs:
- `API_CONTRACT.md` for partner-facing payloads
- normalized `GET /api/sessions/{id}` response contract
- new `GET /api/captures/{id}` endpoint
- clear field-level expectations for taxonomy, palette, tags, reference matches, and nullability

### 2. Demo Dataset and Output Quality
Goal: make the backend outputs look credible in the demo.

Key outputs:
- seed 30–40 strong demo captures/references
- evaluate taxonomy quality on seeded images
- identify obviously wrong label/reference results and tune data/prompt/config where possible
- document known weak cases so the demo path can avoid them

### 3. Clustering and Exploration APIs
Goal: let the partner app show grouped inspiration rather than only flat capture lists.

Key outputs:
- `POST /api/clusters/run`
- `GET /api/clusters`
- simple cluster payload keyed off existing embeddings and session/capture data
- practical cluster summaries suitable for gallery/group views

### 4. Generation and Reflection Layer
Goal: add lightweight language features that improve the story of the session.

Key outputs:
- `POST /api/generate` for short inspiration/prompt generation
- `GET /api/sessions/{id}/reflection` for concise session takeaways
- best-effort fallback behavior when Gemini is unavailable

### 5. Deployment, Health, and Demo Reliability
Goal: make the backend safe to share and resilient in front of other people.

Key outputs:
- Railway deployment plan and live URL handoff
- richer `/api/health` coverage
- Supabase Realtime hookup for captures if time allows
- capture latency improvement work toward `<3s`
- smoke checklist and backup-demo readiness

## Recommended Sequence
1. Lock the API contract and normalize read payloads
2. Seed/demo-test enough captures to expose quality gaps early
3. Add capture detail and clustering endpoints
4. Add generation/reflection only after the read path is stable
5. Finish deployment, health, and observability work last

## What Not To Prioritize Right Now
- Supabase Auth migration
- large taxonomy redesigns
- broad ingestion pipelines
- speculative personalization or preference modeling
- frontend-specific workarounds that belong in a stable API contract instead

## Exit Criteria
The current plan is successful when:
- the partner can build directly against documented backend payloads
- a seeded demo dataset produces believable taxonomy/reference outputs
- sessions and captures can be browsed individually and in clusters
- Gemini failures degrade gracefully without blocking capture/session flows
- the backend is deployed and smoke-checked for demo use
