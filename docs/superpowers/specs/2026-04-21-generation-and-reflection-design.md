# Generation And Reflection Design

## Problem

The backend needs two lightweight text-generation surfaces:

- `POST /api/generate` for short narrative text derived from existing capture or session data
- `GET /api/sessions/{id}/reflection` for a 2-3 sentence session recap

Both must be best-effort. Gemini failures or slow responses cannot break existing browsing flows or corrupt persisted data.

## Approaches Considered

### 1. Thin route logic with direct Gemini calls

- Pros: fast to wire up
- Cons: duplicates prompt construction, fallback handling, and source normalization across routes

### 2. New generation helpers inside `gemini_service.py`

- Pros: keeps Gemini concerns in one place, matches existing best-effort tag-generation design, makes route tests simpler
- Cons: requires adding some text-generation prompt and fallback helpers

### 3. New standalone generation service module

- Pros: strongest separation between image tag generation and text generation
- Cons: adds a new service boundary for a small feature and spreads Gemini behavior across files

## Recommendation

Use approach 2.

Reasoning:

- The existing code already treats Gemini as best-effort in `services/gemini_service.py`.
- The new endpoints need the same behavior: short timeout, safe fallback, no persistence side effects.
- Route code should stay focused on fetching session/capture data and returning clear HTTP failures.

## Endpoint Contract

### `POST /api/generate`

Request body:

```json
{
  "kind": "inspiration_prompt | styling_direction | creative_summary",
  "session_id": "string | null",
  "capture_ids": ["string"]
}
```

Rules:

- exactly one source selector is allowed:
  - `session_id`
  - `capture_ids`
- `capture_ids` must be non-empty when used
- source data comes only from existing persisted captures/session rows

Response body:

```json
{
  "kind": "creative_summary",
  "text": "Short render-ready copy.",
  "fallback_used": false,
  "source": {
    "session_id": "session-1",
    "capture_ids": ["capture-1", "capture-2"]
  }
}
```

### `GET /api/sessions/{id}/reflection`

Response body:

```json
{
  "session_id": "session-1",
  "reflection": "Two to three short sentences.",
  "fallback_used": false,
  "capture_count": 2
}
```

Failure behavior:

- missing session: `404`
- session with zero captures: clear client error (`404` with detail explaining the session has no captures)

## Fallback Strategy

- Build deterministic text from top taxonomy labels, layer tags, palette, and reference titles.
- If Gemini fails or times out, return fallback text plus `fallback_used: true`.
- If source data is missing or empty, fail clearly instead of inventing text.

## Implementation Notes

- Add text-generation schemas in `models/gemini.py` for structured JSON responses.
- Add helper functions in `services/gemini_service.py`:
  - source summarization context formatter
  - short-timeout text generation
  - deterministic fallback builders
- Add a new route module for `POST /api/generate`.
- Extend `routes/sessions.py` with reflection read logic only; do not alter existing session endpoints.

## E2E Use Cases

- Happy path: client requests `POST /api/generate` for a valid session and renders returned `text` directly.
- Error path: client requests reflection for a missing or empty session and receives a clear non-500 error.
- Resilience path: Gemini fails and both endpoints still return a usable fallback string.
