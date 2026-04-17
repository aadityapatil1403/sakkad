# Agent Brief E — Validation and Observability

## Mission
Protect the current working backend while the new retrieval layer is added. This workstream owns tests, smoke validation, and lightweight logging/observability for the MVP path.

## Product Context
The backend already works for capture, sessions, and image-first taxonomy. The next-week retrieval work should not regress those paths. This agent is responsible for making the new system demo-safe.

## What You Own
- backend tests for new behavior
- smoke-path validation updates
- lightweight logging / observability additions

## What You Must Not Own
- corpus schema design
- retrieval ranking logic
- route feature design beyond what is needed for validation

## Recommended Files
- `sakad-backend/tests/`
- `sakad-backend/scripts/` for smoke helpers if needed
- small logging additions in routes/services if clearly useful

## Required Coverage
Add or update tests for:
- capture succeeds when Gemini tag generation fails
- capture succeeds when explanation generation fails
- retrieval returns a stable shape
- empty corpus fails safely
- session list still works
- session detail returns enriched captures
- no regression in image-first taxonomy path

## Observability Requirements
Add lightweight visibility for:
- capture success/failure
- Gemini failure rate
- retrieval empty-hit rate

Keep logging practical and demo-oriented, not overbuilt.

## Deliverables
- updated test coverage
- smoke validation path for enriched captures
- minimal logs that help debug demo failures quickly

## Test / Validation
- full backend test suite remains green
- smoke path confirms:
  - taxonomy present
  - palette present
  - reference matches present for most images
  - capture still returns successfully when Gemini is unstable

## Handoff Contract
Other agents should not need to invent their own validation strategy; this workstream should provide the confidence layer for integration.
