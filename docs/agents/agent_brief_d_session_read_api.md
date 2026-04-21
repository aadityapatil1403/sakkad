# Agent Brief D — Session Detail and Web Read API

## Mission
Make the backend usable by the web app for session browsing by adding or refining read APIs that return enriched capture data in a frontend-friendly shape.

## Product Context
The web app needs to show:
- session folders/albums
- captures within a session
- taxonomy and palette
- optional tags
- retrieved references and explanation

Current read surfaces are too thin for that.

## Dependencies
Assume Agent C lands the enriched capture shape and, if applicable, persists it.

## What You Own
- session detail API shape
- read-path integration for enriched captures
- optional gallery response refinement if needed

## What You Must Not Own
- capture ingestion logic
- retrieval service internals
- relationship generation
- corpus schema

## Recommended Files
- `sakad-backend/routes/sessions.py`
- possibly `sakad-backend/routes/gallery.py`
- tests in `sakad-backend/tests/`

## Required Behavior
Provide a session-level read path suitable for the web app, preferably:

`GET /api/sessions/{id}`

Suggested response contents:
- session metadata
- ordered captures
- for each capture:
  - `image_url`
  - `taxonomy_matches`
  - `tags.palette`
  - optional `layer1_tags`
  - optional `layer2_tags`
  - `reference_matches`
  - `reference_explanation`

## Implementation Requirements
- Keep response shapes simple and frontend-friendly.
- Avoid making the frontend perform multiple follow-up joins if possible.
- Use persisted capture enrichment when available.
- Do not add relationship statements yet; that is a later workstream.

## Deliverables
- session detail endpoint or equivalent enriched read path
- tests for:
  - valid session detail response
  - missing session handling
  - enriched capture presence in the response

## Test / Validation
- session list still works
- session detail returns enriched captures
- response is stable enough for frontend integration

## Handoff Contract
The frontend should be able to consume the session response directly for the end-of-week demo without additional backend changes.
