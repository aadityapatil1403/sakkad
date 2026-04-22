# Agent Brief — Generation and Session Reflection

## Mission
Add lightweight text-generation endpoints that help narrate captures and sessions without becoming critical-path dependencies.

## Product Context
The current backend already uses Gemini in best-effort mode for tags. The next useful layer is short-form generation that improves the design-storytelling value of the app.

## What You Own
- `POST /api/generate`
- `GET /api/sessions/{id}/reflection`
- prompt/summary contract
- fallback behavior when Gemini is unavailable or slow

## What You Must Not Own
- retrieval redesign
- clustering implementation
- deployment setup
- auth and permissions work

## Recommended Files
- `sakad-backend/routes/`
- `sakad-backend/services/gemini_service.py`
- new models/schemas if needed
- tests under `sakad-backend/tests/`

## Required Behavior
`POST /api/generate` should produce concise, useful output from existing capture/session data, for example:
- inspiration prompts
- styling directions
- short creative summaries

`GET /api/sessions/{id}/reflection` should produce a brief 2–3 sentence summary using the session's captures, taxonomy, and references.

## Implementation Requirements
- all Gemini features remain best-effort
- failures must not corrupt persisted data
- outputs should be short, readable, and demo-friendly
- do not let generation block core capture/session browsing

## Deliverables
- generation endpoint contract
- session reflection endpoint contract
- tests for success and Gemini-failure fallback

## Test / Validation
- endpoints return usable text on valid inputs
- empty or missing sessions fail clearly
- Gemini failure returns a safe fallback or null result rather than a server crash

## Handoff Contract
Frontend consumers should be able to render generated text directly without additional backend formatting work.
