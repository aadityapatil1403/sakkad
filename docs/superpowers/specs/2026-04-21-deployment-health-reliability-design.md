# Deployment Health And Reliability Design

**Date:** 2026-04-21  
**Status:** Approved

## Context
The backend already serves capture, session, gallery, and read endpoints locally. The next demo risk is operational rather than product scope: the team needs a deployment-ready runbook, health output that reflects real dependencies, and a reproducible smoke path that proves the partner demo flow still works after deployment.

## Requirements
- keep the existing product APIs unchanged outside health/readiness scope
- expose dependency-aware health information for the live demo
- distinguish healthy vs degraded behavior clearly for operators
- document a Railway deployment path that is reproducible
- provide a smoke procedure covering upload, capture insert, session fetch, and at least one read endpoint
- capture current latency bottlenecks and mitigations for the demo handoff

## Approaches Considered

### 1. Expand `routes/health.py` inline only
Pros:
- smallest code footprint
- no new service abstraction

Cons:
- mixes route wiring with dependency probing logic
- harder to unit test degraded-state combinations
- encourages duplicated logic across `/api/health` and `/api/health/supabase`

### 2. Add a dedicated health-check service and keep routes thin
Pros:
- isolates dependency probing and status aggregation
- supports focused tests for healthy, degraded, and failed states
- lets smoke tooling and docs align to one health contract

Cons:
- adds one new service file
- slightly more up-front design work

### 3. Add separate liveness/readiness endpoints and leave existing routes mostly unchanged
Pros:
- clean operational separation
- common deployment pattern

Cons:
- larger API surface than the brief requires
- risks introducing new partner-visible endpoints without strong need
- unnecessary if the existing routes can return richer diagnostics safely

## Recommendation
Choose approach 2.

It keeps the implementation inside the brief while preserving the current route surface. `/api/health` can remain the operator entry point, `/api/health/supabase` can reuse the same checks for dependency-specific detail, and the actual probing logic can live in a small service module with deterministic tests.

## Planned Artifacts
- `sakad-backend/services/health_service.py`
- `sakad-backend/routes/health.py`
- `sakad-backend/tests/test_health_api.py`
- `sakad-backend/scripts/smoke_demo_flow.sh`
- `docs/deployment_runbook.md`
- `sakad-backend/Procfile`

## Design Notes
- `status` should be one of `ok`, `degraded`, or `error`
- degraded means the API process is live but one or more demo dependencies are not fully ready
- health output should include dependency names, readiness booleans, and actionable error messages
- dependency coverage should include database, storage, taxonomy/model readiness, and Gemini configuration state
- Gemini should be reported distinctly because capture can still function without it; that is a degraded mode, not a full outage
- health checks should avoid mutating state and should prefer lightweight probes over full inference
- smoke validation should create a session, upload a known test image, fetch session detail, fetch sessions list, and hit at least one read endpoint (`GET /api/captures/{id}` or `GET /api/gallery`)

## Plan Review
P0/P1/P2 findings: none on the final pass.
P3:
- keep the smoke script shell-only so it runs on Railway-connected laptops without extra project dependencies
