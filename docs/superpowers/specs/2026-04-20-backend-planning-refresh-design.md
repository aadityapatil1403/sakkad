# Backend Planning Refresh Design

**Date:** 2026-04-20  
**Status:** Approved

## Context
The previous planning pack was written for an earlier backend phase where reference corpus, retrieval, and session detail were still missing. The actual codebase has since advanced beyond that state. The planning docs therefore needed a refresh so the team does not organize work around already-completed milestones.

## Approaches Considered

### 1. Minimal update to the old docs
Pros:
- least writing
- preserves existing filenames and structure

Cons:
- keeps the stale retrieval-first framing
- risks future workers following already-completed workstreams
- does not create a clean "current truth" artifact

### 2. Replace only the weekly plan
Pros:
- quick
- enough for immediate execution

Cons:
- leaves the old agent briefs pointing at obsolete work
- no durable overall roadmap artifact
- weak handoff for parallel work

### 3. Replace the full planning pack with current-state documents
Pros:
- aligns docs with the real backend state
- creates a clean overall roadmap plus focused workstream briefs
- preserves the prior operating model of weekly plan + agent briefs

Cons:
- more up-front writing
- requires updating continuity/changelog as well

## Recommendation
Choose approach 3.

The backend is now in a different phase, so partial edits would leave too much stale guidance in the repo. The right move is to replace the old retrieval-week planning pack with:
- one current overall roadmap
- one refreshed next-week backend plan
- five descriptive agent briefs aligned to the actual remaining gaps

## Resulting Artifact Set
- `current_plan_overall.md`
- `next_week_backend_plan.md`
- `agent_brief_api_contract_and_read_surfaces.md`
- `agent_brief_demo_dataset_and_quality.md`
- `agent_brief_clustering_endpoints.md`
- `agent_brief_generation_and_reflection.md`
- `agent_brief_deployment_health_and_reliability.md`

## Design Principles
- reflect the backend as it exists today, not as it existed last week
- prioritize partner-facing contract clarity and demo reliability
- keep Gemini features best-effort
- keep workstreams discrete enough for parallel execution
- explicitly call out non-goals to control scope
