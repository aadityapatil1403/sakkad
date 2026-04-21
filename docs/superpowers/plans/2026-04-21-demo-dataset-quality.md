# Implementation Plan: Demo Dataset Quality

Date: 2026-04-21
Owner: Codex

## Scope

Implement manifest-driven demo dataset seeding and evaluation without changing route code or API contracts.

## Steps

1. Add a manifest file for the target 30-40 demo captures.
   Success criteria:
   - Covers all requested aesthetic buckets
   - Distinguishes available local images from placeholder/manual-add items
   - Maps each entry to one of `session_fashion`, `session_abstract`, `session_mixed`

2. Add failing tests for the seeding/evaluation helper behavior.
   Success criteria:
   - Tests assert missing-file handling
   - Tests assert alias-to-session-id mapping behavior
   - Tests assert taxonomy/reference weak-case flagging
   - Tests assert markdown/report row generation or equivalent summary shape

3. Implement `scripts/seed_demo_captures.py`.
   Success criteria:
   - Reads the manifest
   - Creates three demo sessions through the app
   - Uploads source assets to `specs-bucket`
   - Calls `POST /api/capture` for available files
   - Prints per-image evaluation output and overall summary

4. Expand `test-images/` support files only as safe in-repo placeholders.
   Success criteria:
   - Existing real images remain usable
   - Placeholder filenames are represented in the manifest and docs
   - No hidden dependency on unavailable downloads

5. Write `docs/eval_demo_dataset.md`.
   Success criteria:
   - Includes table: image | expected taxonomy | actual top match | pass/fail
   - Includes weak cases with notes
   - Includes missing/manual assets list
   - Includes 3-5 safest live-demo recommendations

6. Verify.
   Success criteria:
   - `python -m pytest tests/ -x -q` passes
   - `python scripts/seed_demo_captures.py` runs as far as the current environment allows
   - Any environment blocker is recorded explicitly in docs and `CONTINUITY.md`

## E2E

N/A for automated E2E. Manual verification is the script run itself against the real app stack and Supabase project.

## Plan Review

Initial self-review findings:
- P1: The plan must not attempt to persist non-UUID session aliases into `captures.session_id`; alias mapping has to be internal to the script.
- P1: The plan must treat `specs-bucket` upload as additional source-asset mirroring, not as a replacement for the current `/api/capture` storage path.
- P2: The evaluation output should be machine-readable enough that `docs/eval_demo_dataset.md` can be updated without reinterpreting console text by hand.

Plan adjustment:
- Session aliases will map to started session UUIDs at runtime.
- The seeding script will upload to `specs-bucket` first, then call `/api/capture`.
- The script will produce a structured summary object and a markdown snippet writer/helper for the docs workflow.
