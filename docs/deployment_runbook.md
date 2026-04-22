# Deployment Runbook

## Goal
Make the Sakkad backend safe to share for a live partner demo by making deployment repeatable, health states diagnosable, and the core capture flow easy to smoke-test after every deploy.

## Railway Checklist

1. Create a Railway service rooted at `sakad-backend/`.
2. Use the included `Procfile` entrypoint so Railway runs:
   `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Set the required environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `CLIP_MODEL_NAME` if different from the default
   - `TAXONOMY_EMBEDDING_MODEL` if different from the default
   - `GEMINI_API_KEY` for full demo mode
   - `GEMINI_MODEL` / `GEMINI_FALLBACK_MODELS` as needed
4. Choose a Railway plan with enough RAM for SigLIP. The project continuity target is 8 GB.
5. Confirm the Supabase project already has:
   - `captures` bucket
   - `captures`, `sessions`, and `taxonomy` tables
   - taxonomy embeddings seeded with `scripts/seed_taxonomy.py`
6. Deploy once, then run the smoke flow against the Railway URL:
   `bash scripts/smoke_demo_flow.sh https://<railway-url>`

## Health Endpoints

### `GET /api/health`
- `status=ok`: all checks (required and optional) are passing
- `status=degraded`: required checks passed, but a non-critical dependency is unavailable
- `status=error`: one or more critical demo dependencies failed; treat the deploy as unsafe

Checks currently reported:
- `database`: read probe against the `captures` table
- `storage`: list probe against the `captures` bucket
- `taxonomy`: taxonomy availability plus SigLIP configuration/lazy-load state
- `gemini`: configuration state only; capture still works without it, but tags/reference explanation quality degrades

### `GET /api/health/supabase`
Focused view of the database and storage checks, with only Supabase-related errors included.

## Smoke Procedure

Run from `sakad-backend/`:

```bash
bash scripts/smoke_demo_flow.sh http://127.0.0.1:8000
```

What it validates:
- `/api/health` is not in `error`
- `POST /api/sessions/start` creates a session
- `POST /api/capture` uploads an image and inserts a capture for that session
- `GET /api/sessions/{id}` returns the inserted capture
- `GET /api/sessions` lists the new session
- `GET /api/captures/{id}` returns the normalized read payload

Recommended demo image:
- default: `western.jpg`
- alternatives: `workwear.jpg`, `furcoat.jpg`

## Failure Playbook

If `/api/health` reports `error`:
- `database` failed: verify `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, table existence, and network access from Railway
- `storage` failed: verify the `captures` bucket exists and the service key has storage access
- `taxonomy` failed: re-run `python scripts/seed_taxonomy.py` in a configured environment and confirm embedding model alignment

If `/api/health` reports `degraded`:
- `gemini` failed: the demo can proceed, but expect weaker tag enrichment and missing reference explanations

If smoke capture fails:
- inspect Railway logs for `[capture]` lines; the route already logs upload, insert, and enrichment failures
- verify the uploaded image is reaching Supabase storage
- confirm the capture row appears in Supabase with `session_id`

## Current Latency And Reliability Notes

### Bottlenecks
- First capture after process start is the slowest path because SigLIP loads lazily on first inference.
- Capture latency includes three remote/network segments: Supabase storage upload, Supabase row insert, and optional Gemini calls.
- Gemini is the highest-variance dependency. It can fail or rate-limit independently of the core capture path.

### Best Mitigations
- Warm the deploy before the demo by running `bash scripts/smoke_demo_flow.sh <url>` once.
- Keep Gemini best-effort. The health endpoint surfaces when the deploy is in degraded mode without blocking the demo.
- Use known-good demo images from `test-images/` for the live validation pass.
- Check `/api/health` before sharing the URL with the partner and again immediately before the demo.

## Optional Next Step
Supabase Realtime on `captures` is still optional. It is not required for this runbook and was intentionally left out of the deployment-critical path.
