# Agent Brief — API Contract and Read Surfaces

## Mission
Turn the existing backend into a partner-consumable API surface by documenting and normalizing the read contracts.

## Product Context
Capture enrichment and session detail are already in place. The problem is no longer missing core retrieval; it is making the current payloads stable, documented, and easy for the web app to consume.

## What You Own
- `API_CONTRACT.md`
- response-shape review for `GET /api/sessions`, `GET /api/sessions/{id}`, `GET /api/gallery`
- design and implementation plan for `GET /api/captures/{id}`
- nullability and field consistency for enriched capture payloads

## What You Must Not Own
- clustering internals
- Gemini prompt-generation features
- large taxonomy tuning work
- deployment setup

## Recommended Files
- `sakad-backend/routes/sessions.py`
- `sakad-backend/routes/gallery.py`
- `sakad-backend/routes/` for new capture detail route if needed
- new `API_CONTRACT.md` at repo root or backend root
- tests under `sakad-backend/tests/`

## Required Behavior
The partner should be able to rely on one stable enriched capture shape across list/detail endpoints, including:
- `id`
- `session_id`
- `image_url`
- `created_at`
- `taxonomy_matches`
- `tags.palette`
- `layer1_tags`
- `layer2_tags`
- `reference_matches`
- `reference_explanation`

Add `GET /api/captures/{id}` if it is still missing.

## Deliverables
- written API contract
- endpoint audit showing what already matches the contract and what does not
- any minimal route/test changes needed to normalize the payloads

## Test / Validation
- session list still works
- session detail stays backward-compatible for the web app
- capture detail returns the same enriched shape as session detail
- missing optional fields normalize cleanly

## Handoff Contract
All downstream workstreams should treat this contract as the source of truth for read payloads.
