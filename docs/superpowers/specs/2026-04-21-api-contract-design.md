# API Contract Design — 2026-04-21

## Goal

Normalize backend read endpoints so the partner web app can rely on one stable enriched capture shape across gallery, session detail, and capture detail reads.

## Audit Summary

- `GET /api/gallery` currently returns raw `captures` rows, so fields are not normalized and optional keys may be absent.
- `GET /api/sessions` currently returns session rows only, not capture-shaped objects. It cannot satisfy the required capture contract because its resource is different.
- `GET /api/sessions/{id}` already returns enriched captures, but the shape is incomplete:
  - `tags` only includes `palette`
  - missing optional fields normalize to empty arrays in several places instead of explicit nullable keys
  - normalization logic is route-local instead of shared

## Approaches

### A. Normalize independently inside each route

Pros:
- smallest immediate diff

Cons:
- repeats contract logic
- easy for route drift to reappear
- makes the new capture detail endpoint another copy

### B. Add shared read-side capture serializer and use it across all capture-returning endpoints

Pros:
- single source of truth for the partner contract
- easiest way to keep gallery, session detail, and capture detail aligned
- low-risk change limited to read surfaces

Cons:
- requires touching multiple route files at once

### C. Introduce Pydantic response models for every endpoint

Pros:
- explicit schema validation

Cons:
- larger refactor than required
- slower path for a small stabilization task

## Recommendation

Choose Approach B. Add one shared serializer that:
- returns every required key for capture reads
- coerces `taxonomy_matches` into `dict[str, float]`
- keeps optional keys present with `null` defaults unless a container is clearly more useful and already required by contract
- normalizes reference items to the documented subset

`GET /api/sessions` should remain a session-list endpoint, but the audit should document that it does not and should not return the capture shape because it is a different resource.

## Planned Behavior

- `GET /api/gallery`: return a list of normalized captures
- `GET /api/sessions/{id}`: return session metadata plus normalized captures
- `GET /api/captures/{id}`: return one normalized capture or `404`
- `GET /api/sessions`: remain session metadata, documented separately in the contract

## E2E Use Cases

- Happy path: partner loads gallery, session detail, or single capture and receives the same enriched capture keys everywhere captures appear.
- Error path: partner requests a missing capture id and receives `404 {"detail": "Capture not found"}`.
