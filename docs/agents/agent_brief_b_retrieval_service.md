# Agent Brief B — Retrieval Service

## Mission
Build the retrieval service that maps a capture `image_vec` to ranked designer/reference matches from the curated corpus.

## Product Context
The MVP is retrieval-first. Image-first SigLIP taxonomy stays as the production backbone. This workstream adds the missing reference-intelligence layer on top of that backbone.

## Dependencies
Assume Agent A defines the reference corpus schema and seed format. If exact field names differ, adapt to the schema Agent A lands, but do not redesign it.

## What You Own
- Retrieval service implementation
- Ranked result shape
- Retrieval service tests
- Optional in-memory cache for reference embeddings if clearly useful

## What You Must Not Own
- Capture route integration
- Explanation generation
- Session read APIs
- Corpus schema redesign

## Recommended Files
- new service module under `sakad-backend/services/`
- tests under `sakad-backend/tests/`

## Required Service Contract
Provide a service-level API equivalent to:

`get_reference_matches(image_embedding: list[float], limit: int = 5) -> list[dict]`

Suggested result shape:
- `id`
- `designer`
- `brand`
- `collection_or_era`
- `title`
- `description`
- `image_url`
- `score`

## Implementation Requirements
- Use the existing SigLIP-centered architecture.
- Retrieval should be similarity-based and deterministic.
- Keep the result shape stable and easy for route consumers to use.
- Handle empty/missing corpus safely.
- If you add caching, keep it local and simple, similar in spirit to the taxonomy cache.

## Deliverables
- retrieval service module
- tests for:
  - normal ranking
  - empty corpus
  - malformed or missing embeddings
  - limit handling

## Test / Validation
- given a valid image embedding, the service returns top matches in a stable order
- empty corpus returns an empty list rather than throwing
- malformed rows do not crash the request path

## Handoff Contract
Agent C should be able to import one stable retrieval function/service and use it directly from `/api/capture`.
