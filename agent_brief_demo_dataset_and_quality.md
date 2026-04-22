# Agent Brief — Demo Dataset and Output Quality

## Mission
Seed and validate the demo dataset so taxonomy, references, and future clusters look believable during the live walkthrough.

## Product Context
The backend now has the plumbing for classification and references. The main risk is not missing code; it is weak demo outputs from sparse or low-quality seeded data.

## What You Own
- seeding 30–40 demo-quality captures/references
- evaluation of taxonomy/reference outputs on those samples
- identification of weak labels or obvious mismatches
- lightweight tuning recommendations grounded in observed failures

## What You Must Not Own
- API contract design
- clustering endpoint implementation
- deployment or infra work
- auth changes

## Recommended Files
- `data/`
- `sakad-backend/scripts/`
- `sakad-backend/eval/`
- `sakad-backend/test-images/`
- docs under `docs/` for evaluation notes if helpful

## Required Output
Create a small but strong demo dataset that covers multiple aesthetic buckets the partner can show confidently, such as:
- workwear / utility
- western / americana
- sporty streetwear
- monochrome / minimal
- archival or designer-reference looks

## Deliverables
- updated or expanded seed assets/data
- a short evaluation summary of strong vs. weak cases
- recommendations for which images/look-types are safest for the demo

## Test / Validation
- seeded data loads reproducibly
- taxonomy matches are present and plausible for most demo assets
- reference matches are available for most seeded captures
- clearly bad outputs are documented rather than hand-waved

## Handoff Contract
Clustering and web-demo workstreams should use this dataset as the default smoke and demo corpus.
