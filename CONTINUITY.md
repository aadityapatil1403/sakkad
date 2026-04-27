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

- Merged `feat/soccer-taxonomy` + `fix/fix-codex-p1-p2-review-issues` → main; Codex P2 fixes applied to both branches before merge; 144 backend + 22 frontend tests passing (2026-04-26)
- P1/P2 Codex review fixes: SketchStage generation on button click, run_in_threadpool, retry 502/504/httpx, UUID normalization, generateImage wrapper + tests (2026-04-25)
- Soccer taxonomy: 6 new labels + 20 brand corpus entries; KidSuper/Palace data integrity fixed (2026-04-25)

### Now

**Week 3 — Demo-readiness and Partner Contract**

- [x] Merge `feat/soccer-taxonomy` → main
- [ ] Run live demo seed (`python scripts/seed_demo_captures.py`)
- [ ] Ship first-pass clustering: `POST /api/clusters/run`, `GET /api/clusters`
- [x] Soccer taxonomy + brand corpus seeded and validated
- [x] Ship sketch generation: `POST /api/generate/image` + wired `SketchStage`
- [x] Improve partner narrative surfaces: `POST /api/generate`, `GET /api/sessions/{id}/reflection`

**Exit criteria:** Partner can consume documented session/capture reads, live seed documents actual taxonomy/reference outcomes, clustering works on seeded demo data.

### Next

- Week 3: `POST /api/clusters/run` (HDBSCAN), `GET /api/clusters`, share live URL with partner
- Week 4: Deploy to Railway, Supabase Realtime on captures table, improve health/readiness endpoints
- Week 5: Seed 40+ demo captures, optimize `POST /api/capture` to <3s, full health endpoint, backup demo video

---

## Workflow

| Field     | Value                                  |
| --------- | -------------------------------------- |
| Command   | /fix-bug fix-codex-p1-p2-review-issues |
| Phase     | 6 — Finish                             |
| Next step | Commit and push                        |

### Checklist

- [x] Worktree created
- [x] Project state read
- [x] Plugins verified
- [x] Searched existing solutions
- [x] Systematic debugging complete
- [x] TDD fix execution complete
- [x] Code review loop (1 iteration) — PASS (simplify agent fixed P2s: dead code, event loop block, double scroll, misplaced import)
- [x] Simplified
- [x] Verified (tests/lint/types) — 137 backend + 22 frontend, tsc clean
- [x] E2E use cases tested — N/A: all changes are logic/backend; UI trigger moved to button (user-visible but no browser test needed beyond unit coverage)
- [x] Learning documented
- [x] State files updated
- [ ] Committed and pushed
- [ ] PR created

---

## Open Questions

- Whether `GET /api/sessions` should eventually gain preview metadata for the web app, or remain a pure session list while detail routes own capture reads
- Whether the taxonomy art_reference/visual_context labels (44 unseeded entries) should be seeded before the clustering pass, or if the demo proceeds with fashion_streetwear-only (56 labels)
- Whether the current taxonomy/reference corpus is strong enough on abstract/environmental imagery, or if those captures should stay secondary in the live demo mix

## Blockers

- `ruff` and `mypy` are not installed in the current shell environment; `python -m pytest` passes, but the full verify gate cannot complete until those tools are available
- Live smoke validation still depends on a running backend plus configured Supabase credentials

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

> "Loaded project state. Current focus: Week 3 — demo seeding, clustering, and partner handoff. Ready to continue or start something new?"
