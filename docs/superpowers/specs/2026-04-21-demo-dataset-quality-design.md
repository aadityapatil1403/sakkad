# Demo Dataset Quality Design

Date: 2026-04-21
Owner: Codex
Brief: `/Users/aaditya/Desktop/XR_Fashion/sakkad/agent_brief_demo_dataset_and_quality.md`

## Goal

Create a reproducible demo dataset workflow for the Sakkad backend that:

- defines a 30-40 capture corpus across the requested aesthetic buckets
- seeds available assets through the existing session + capture pipeline
- evaluates top taxonomy/reference quality per capture
- documents weak cases and recommends the safest live-demo images

## Constraints

- Do not change route files, API contract, clustering, or deployment.
- `/api/capture` currently uploads into the `captures` bucket. The task also asks to upload source assets into `specs-bucket`.
- Session ids in the database are UUID-backed, so friendly names like `session_fashion` must be aliases mapped to real session ids.
- Network access may prevent direct asset downloads in this environment.

## Existing Code Reality

- `sakad-backend/routes/capture.py` accepts multipart form upload and optional `session_id`.
- `sakad-backend/routes/sessions.py` can create sessions via `/api/sessions/start`.
- Existing evaluation tooling already posts real images to `/api/capture` and inspects `taxonomy_matches` as a dict plus `reference_matches` as a list.
- `sakad-backend/test-images/` currently contains 10 usable images, not the requested 30-40 corpus.

## Approach Options

### A. Hard-code a one-off script around the current 10 images

Pros:
- Fastest to write
- Minimal surface area

Cons:
- Fails the 30-40 corpus requirement
- No clear way to track missing/manual assets
- Weak handoff for future demo prep

### B. Manifest-driven dataset with placeholders and optional downloads

Pros:
- Reproducible source of truth for 30-40 intended captures
- Supports current local images plus missing/manual asset placeholders cleanly
- Lets the seeding script skip unavailable files while still reporting gaps
- Keeps evaluation and documentation tied to the same manifest

Cons:
- Slightly more upfront structure
- Initial runtime seeding may cover fewer than 30-40 captures until assets are added

### C. Add a database-side seed flow that bypasses `/api/capture`

Pros:
- More control over storage/session inserts

Cons:
- Violates the brief's requirement to run the full enrichment pipeline
- Higher risk of drifting from the real demo path

## Recommendation

Use Approach B.

It satisfies the brief without modifying protected route code. A manifest can define the full target demo corpus immediately, while the script seeds any locally available assets now and clearly reports missing files that still need manual download.

## Proposed Deliverables

1. `sakad-backend/eval/demo_dataset_manifest.json`
   Defines 30-40 target captures with:
   - filename
   - bucket/session alias
   - local path
   - aesthetic bucket
   - expected taxonomy labels
   - source metadata
   - availability status

2. `sakad-backend/scripts/seed_demo_captures.py`
   Responsibilities:
   - read manifest
   - ensure three demo sessions exist by creating them through `/api/sessions/start`
   - upload available source files to `specs-bucket`
   - call `/api/capture` for each available image
   - print top taxonomy and top reference
   - flag wrong taxonomy and low reference scores
   - emit a machine-readable summary for docs follow-up

3. `sakad-backend/tests/test_seed_demo_captures.py`
   TDD coverage for manifest handling, session alias mapping, flagging logic, and report generation

4. `docs/eval_demo_dataset.md`
   Evaluation table, weak-case notes, missing/manual asset list, and recommended safest demo images

## Evaluation Rules

- Top taxonomy is a pass if it matches one of the manifest's expected or acceptable labels.
- Top reference is weak if the list is empty, the top score is `<= 0.0`, or falls below a small warning threshold.
- Missing local assets are not silent skips; they must be listed in the report.

## E2E

N/A for automated E2E. This is internal seeding/evaluation tooling, but it exercises the real `/api/sessions/start` and `/api/capture` pipeline during manual run.
