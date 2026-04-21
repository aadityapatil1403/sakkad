# API Contract Implementation Plan — 2026-04-21

## Scope

Stabilize read contracts for capture-oriented endpoints without changing ML, Gemini, clustering, seeding, or deployment code.

## Steps

1. Add a shared capture read serializer.
   - Normalize every required capture key.
   - Ensure `taxonomy_matches` always returns an object.
   - Ensure optional keys are present with `null` when missing.

2. Update existing read routes to use the shared serializer.
   - Normalize `GET /api/gallery`.
   - Keep `GET /api/sessions` as a session-list endpoint and document it accordingly.
   - Normalize capture objects nested under `GET /api/sessions/{id}`.

3. Add `GET /api/captures/{id}`.
   - Query one capture by id.
   - Return the shared normalized shape.
   - Return `404` when no row is found.

4. Add and update tests using TDD.
   - Add failing tests for capture detail happy path and `404`.
   - Add response-shape assertions that `taxonomy_matches` is an object in gallery, session detail, and capture detail responses.

5. Rewrite backend-local `API_CONTRACT.md`.
   - Cover each endpoint’s method, path, request shape, and response shape.
   - Mark nullable fields explicitly.
   - Include audit notes for endpoints that do not return captures.

## Plan Review

### Findings

- P0: none
- P1: none
- P2: none
- P3: keep `GET /api/sessions` session-focused rather than forcing it into a capture contract it cannot represent cleanly

Plan passes review and is ready for TDD execution.
