# Agent Brief C — Capture Route Enrichment

## Mission
Enrich the existing capture pipeline with reference retrieval and a short explanation field, without destabilizing the current image-first classifier.

## Product Context
The capture route already does:
- image upload
- image embedding
- image-first taxonomy classification
- palette extraction
- optional Gemini `layer1` / `layer2`

This workstream adds:
- `reference_matches`
- `reference_explanation`

## Dependencies
Assume Agent B provides a retrieval service contract for `image_vec -> reference matches`.

## What You Own
- `/api/capture` route integration
- response shape additions
- persistence of new enriched fields if needed
- explanation wiring and fallback behavior

## What You Must Not Own
- classifier redesign
- taxonomy logic changes
- session detail/read APIs
- relationship generation

## Recommended Files
- `sakad-backend/routes/capture.py`
- optional helper service for explanation generation under `sakad-backend/services/`
- tests in `sakad-backend/tests/`

## Required Behavior
After `image_embedding` is available:
1. classify taxonomy as today
2. retrieve reference matches from the retrieval service
3. generate a short `reference_explanation` using:
   - taxonomy
   - top reference matches
   - optional `layer1` / `layer2` if present

Suggested new response fields:
- `reference_matches`
- `reference_explanation`

## Implementation Requirements
- Keep image-first taxonomy unchanged this week.
- All LLM-based explanation must be best-effort.
- If Gemini fails:
  - capture must still succeed
  - taxonomy must still return
  - reference retrieval must still return
  - `reference_explanation` may be `null`
- Do not make retrieval or explanation block the whole route on transient LLM failure.

## Persistence Guidance
Prefer persisting enriched output in `captures` if that simplifies later session/detail reads. If you add DB fields, keep the shape straightforward and demo-oriented.

## Deliverables
- enriched `POST /api/capture` response
- optional persistence of reference enrichment
- tests for:
  - successful capture with references
  - Gemini explanation failure fallback
  - retrieval empty result fallback

## Test / Validation
- `/api/capture` still succeeds when Gemini tag generation fails
- `/api/capture` still succeeds when explanation generation fails
- reference matches appear in successful captures
- taxonomy behavior does not regress

## Handoff Contract
Agent D should be able to read enriched capture rows or capture payloads without reimplementing retrieval logic.
