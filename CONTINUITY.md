# CONTINUITY

## Goal

Build the Sakkad backend (FastAPI + SigLIP + Supabase) so Snap Spectacles can capture fashion inspiration, classify it against a 100-label taxonomy, and surface clusters on a partner-built web app — live demo in 4 weeks.

## Key Decisions

| Decision      | Choice                                    | Why                                                                                 |
| ------------- | ----------------------------------------- | ----------------------------------------------------------------------------------- |
| Vision model  | SigLIP (`google/siglip-base-patch16-224`) | Sigmoid loss scores each label independently — essential for multi-aesthetic images |
| Taxonomy size | ~100 labels across 3 tiers                | Fashion/Streetwear (~50), Visual/Environmental (~30), Visual Art/Reference (~20)    |
| Auth          | DEV_USER_ID hardcoded                     | MVP speed — Supabase Auth only post-demo if time allows                             |
| Deploy        | Railway $5/mo 8GB RAM                     | SigLIP is 813MB; needs RAM headroom                                                 |
| Gemini        | Backend-proxied only                      | No API keys exposed to Lens Studio or web frontend                                  |
| Clustering    | HDBSCAN on SigLIP embeddings              | Density-based, no fixed k — better for fashion aesthetic clusters                   |

---

## State

### Done (recent)

- Review findings fixed: session detail now degrades safely on legacy databases missing `captures.session_id`, retrieval retries after transient corpus-load errors, and `seed_reference_corpus.py` deletes stale rows only after successful upserts (2026-04-21)
- Backend refactor implemented: extracted `color_service.py` and `enrich_service.py`, moved taxonomy classification into `clip_service.py`, and slimmed `routes/capture.py` to storage + insert orchestration (2026-04-21)
- Capture contract migrated: `taxonomy_matches` now stores/returns `dict[str, float]`; sessions fixtures, capture tests, classifier eval, and smoke scripts updated to match (2026-04-21)
- Markdown reorg completed: agent briefs/plans/worktree notes moved under `docs/`, plus new root `README.md` and `API_CONTRACT.md` added (2026-04-21)

### Now

**feat/backend-refactor — Final Verification**

- [x] Implement six-task backend refactor plan
- [x] Run full pytest suite in worktree (`81 passed`)
- [ ] Run `ruff check .` in an environment where Ruff is installed
- [ ] Run `mypy --strict .` in an environment where mypy is installed
- [ ] Commit and push branch once remaining verify tools are available

**Exit criteria:** pytest/lint/type-check all pass, then branch is ready to commit/push.

### Next

- Week 3: `GET /api/captures/{id}`, `POST /api/clusters/run` (HDBSCAN), `GET /api/clusters`, `POST /api/generate` (Gemini), seed 30+ demo captures, share live URL with partner
- Week 4: Deploy to Railway, Supabase Realtime on captures table, `GET /api/sessions/{id}/reflection`
- Week 5: Seed 40+ demo captures, optimize `POST /api/capture` to <3s, full health endpoint, backup demo video

---

## Workflow

| Field     | Value                         |
| --------- | ----------------------------- |
| Command   | /new-feature backend-refactor |
| Phase     | 5 — Verify                    |
| Next step | Run lint/type tools in a provisioned environment |

### Checklist

- [x] Worktree created (`feat/backend-refactor`)
- [x] Project state read
- [x] Plugins verified
- [x] PRD created — N/A: refactor spec, no new product requirements
- [x] Research done — codebase audit complete, all 64 tests confirmed passing
- [x] Brainstorming complete — Approach C selected (strict 4-service layout)
- [x] Plan written — `docs/superpowers/plans/2026-04-21-backend-refactor.md`
- [x] Plan review loop (1 iteration) — P0/P1 gaps called out and folded into implementation before code changes
- [x] TDD execution complete
- [x] Code review loop (1 iteration) — no remaining P0/P1/P2 findings in changed files
- [x] Simplified
- [ ] Verified (tests/lint/types) — pytest passed; `ruff` and `mypy` unavailable in current shell
- [x] E2E use cases tested — N/A: internal refactor, no user-facing behavior changes
- [ ] Learnings documented (if any)
- [x] State files updated
- [ ] Committed and pushed
- [ ] PR created
- [ ] PR reviews addressed
- [ ] Branch finished

---

## Open Questions

- Whether to keep `taxonomy_matches` as the long-term canonical external contract or add a compatibility adapter for any consumer still expecting ranked arrays
- Taxonomy accuracy is still uneven on some demo images (`western.jpg`, `furcoat.jpg`); likely a taxonomy/data-tuning problem rather than a route/service-structure problem

## Blockers

- `ruff` and `mypy` are not installed in the current shell environment, so the full verify gate cannot complete until those tools are provisioned

---

## Update Rules

> **IMPORTANT:** You (Claude) are responsible for updating this file. The Stop hook will remind you, but YOU must make the edits.

**On task completion:**

1. Add to Done (keep only 2-3 recent items)
2. Move top of Next → Now
3. Add to CHANGELOG.md if significant

**On new feature:**
Clear Done section, start fresh

**Where detailed progress lives:**

- Feature subtasks → `docs/plans/[feature].md`
- Historical record → `docs/CHANGELOG.md`
- Learnings → `docs/solutions/`

---

## Session Start

Claude should say:

> "Loaded project state. Current focus: Week 2 backend core — Sessions API, taxonomy seeding, and classification. Ready to continue or start something new?"
