# Deployment Health And Reliability Implementation Plan

**Goal:** Make the backend demo-safe for deployment by adding dependency-aware health checks, a reproducible Railway runbook, and a smoke flow that validates the live demo path without changing non-health APIs.

## File Map

| File | Status | Change |
| --- | --- | --- |
| `sakad-backend/services/health_service.py` | Create | Aggregate dependency probes and status classification |
| `sakad-backend/routes/health.py` | Modify | Return richer health and Supabase-specific diagnostics |
| `sakad-backend/tests/test_health_api.py` | Create | Cover healthy, degraded, and failed dependency states |
| `sakad-backend/scripts/smoke_demo_flow.sh` | Create | Exercise session start, capture upload, session fetch, and read flow |
| `docs/deployment_runbook.md` | Create | Railway checklist, smoke checklist, latency notes, failure playbook |
| `sakad-backend/Procfile` | Create | Railway-compatible process entrypoint |
| `docs/CHANGELOG.md` | Modify | Record the deployment-health workstream |
| `CONTINUITY.md` | Modify | Track workflow progress and final state |

## Execution Steps

- [ ] Step 1: Write failing health-route tests for healthy, degraded, and error states.
- [ ] Step 2: Implement `services/health_service.py` with dependency probes for database, storage, taxonomy/model readiness, and Gemini configuration.
- [ ] Step 3: Update `routes/health.py` to use the service and return clear status payloads plus `503` only for full error states.
- [ ] Step 4: Run the full backend test suite and keep it at 99 passing tests.
- [ ] Step 5: Add the demo smoke script covering `/api/health`, `/api/sessions/start`, `/api/capture`, `/api/sessions/{id}`, `/api/sessions`, and one read endpoint.
- [ ] Step 6: Add deployment/runbook documentation and Railway `Procfile`.
- [ ] Step 7: Run self-review, simplify if needed, and execute verification gates.

## E2E Use Cases

### Use Case 1: Happy path deploy smoke
Intent: confirm a deployed backend can support the live partner flow.
Steps:
1. Hit `/api/health` and confirm the service is not in `error`
2. Start a session through `/api/sessions/start`
3. Upload a test image through `/api/capture` with that `session_id`
4. Fetch `/api/sessions/{id}` and confirm the uploaded capture is present
5. Fetch `/api/captures/{capture_id}` and confirm the capture can be read back
Verification:
- health payload shows dependency diagnostics
- session creation succeeds
- capture insert succeeds and returns an `id`
- session detail contains the inserted capture
- capture read returns normalized taxonomy/read fields
Persistence:
- the inserted session and capture exist in Supabase and are available to the partner web app

### Use Case 2: Degraded dependency visibility
Intent: confirm operators can distinguish degraded demo mode from a full outage.
Steps:
1. Call `/api/health` with Gemini unset or a non-critical dependency unavailable
2. Inspect the returned health payload
Verification:
- response status is `200`
- payload `status` is `degraded`
- the failing dependency is named explicitly with an actionable message
Persistence:
- no state mutation occurs; this is a read-only operational check
