# Agent Brief — Deployment, Health, and Reliability

## Mission
Make the backend demo-safe once the core endpoints are in place.

## Product Context
A working local backend is no longer enough. The next risk is operational: deployment, health visibility, latency, and failure handling during the demo.

## What You Own
- Railway deployment readiness
- richer `/api/health` coverage
- smoke validation checklist
- capture latency and reliability observations
- optional Supabase Realtime integration for captures if time allows

## What You Must Not Own
- clustering algorithm design
- API payload redesign outside health/readiness needs
- dataset seeding strategy except where needed for smoke checks

## Recommended Files
- `sakad-backend/routes/health.py`
- deployment docs/config where applicable
- smoke scripts under `sakad-backend/scripts/`
- `docs/` notes for runbook-style guidance if needed

## Required Behavior
- provide a health view that reflects the backend's real demo dependencies
- verify database, storage, and any required model/service readiness
- keep demo failure modes diagnosable from logs and health endpoints

## Deliverables
- improved health endpoint or supporting checks
- deployment checklist/runbook
- smoke procedure for capture, sessions, and key read endpoints
- notes on current latency bottlenecks and best mitigations

## Test / Validation
- health checks distinguish healthy vs. degraded states clearly
- smoke path covers upload, capture insert, session fetch, and at least one read flow
- deployment steps are reproducible and documented

## Handoff Contract
Once this workstream is done, the team should know whether the backend is safe to share live with the partner and what to do if it degrades.
