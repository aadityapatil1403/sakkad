# Agent Brief — Clustering Endpoints

## Mission
Add the clustering layer that turns flat captures into grouped inspiration sets for the web app.

## Product Context
The backend already stores embeddings and session-linked captures. The next backend capability gap is grouped exploration: the partner app needs clusters, not just capture lists.

## What You Own
- `POST /api/clusters/run`
- `GET /api/clusters`
- cluster result shape and storage strategy if persistence is needed
- tests for clustering behavior and empty-state handling

## What You Must Not Own
- API contract for non-cluster endpoints
- taxonomy rework
- Gemini generation/reflection features
- deployment work

## Recommended Files
- new route module under `sakad-backend/routes/`
- new service/helper module under `sakad-backend/services/`
- possible migration/model files if cluster persistence is needed
- tests under `sakad-backend/tests/`

## Required Behavior
- cluster off existing capture embeddings
- support running clusters over the demo dataset or session-linked captures
- return simple frontend-friendly cluster payloads
- handle too-few-captures and no-data cases safely

Suggested cluster payload fields:
- `cluster_id`
- `label` or `summary`
- `capture_ids`
- optional representative capture
- cluster size / score metadata

## Deliverables
- initial clustering implementation
- route contract for run + read
- tests covering happy path, too-few-captures, and empty corpus/session cases

## Test / Validation
- clusters can be computed over seeded captures
- responses are stable enough for the frontend to render
- failure and empty states do not crash the API

## Handoff Contract
The web app should be able to request clusters without reimplementing grouping logic client-side.
