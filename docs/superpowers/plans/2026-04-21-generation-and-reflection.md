# Generation And Reflection Plan

## Scope

Implement the brief in these files only unless tests force a narrow supporting change:

- `sakad-backend/models/gemini.py`
- `sakad-backend/services/gemini_service.py`
- `sakad-backend/routes/generate.py`
- `sakad-backend/routes/sessions.py`
- `sakad-backend/main.py`
- `sakad-backend/tests/test_generate_api.py`
- `sakad-backend/tests/test_sessions_api.py`
- `sakad-backend/tests/test_gemini_service.py`
- `sakad-backend/API_CONTRACT.md`

## Plan

1. Write failing route tests for `POST /api/generate`.
   Verify valid session generation, clear failures for missing/empty sources, and fallback on Gemini failure.

2. Write a failing session reflection test.
   Verify `GET /api/sessions/{id}/reflection` returns 2-3 sentence text or a deterministic fallback and fails clearly for missing/empty sessions.

3. Write failing gemini service tests for text-generation helpers.
   Verify schema-backed text parsing and fallback behavior for API exceptions.

4. Implement minimal schemas and Gemini text helpers.
   Keep text short, add a shorter timeout than image-tag generation, and return `None` on Gemini failure so routes can apply deterministic fallbacks.

5. Implement the new generate route.
   Fetch source rows, validate selector rules, build generation context, and return render-ready text with `fallback_used`.

6. Implement the session reflection endpoint.
   Reuse the same capture-normalization/read patterns, then call the text helper with session-specific prompting and deterministic fallback.

7. Update API contract docs.
   Document the request and response contracts for both endpoints.

8. Run review, simplify, and full verification.
   Required checks:
   - `python -m pytest tests/ -x -q` after each edit batch
   - final: `python -m pytest && ruff check . && mypy --strict .`

## Plan Review

P0-P2 review against the live codebase:

- No existing endpoint behavior needs to change; `routes/sessions.py` can safely add one new read-only endpoint.
- `gemini_service.py` already owns Gemini best-effort behavior, so adding text generation there is the simplest consistent choice.
- The current app router registration in `main.py` is minimal and can include one more router without side effects.
- Existing tests patch route-local `supabase`, so new tests should follow the same pattern instead of introducing global fixtures.

Status: clean after 1 review pass.
