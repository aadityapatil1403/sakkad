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

- Review fixes applied to demo seeding: `specs-bucket` upload is now best-effort and generated evaluation docs keep unseeded manifest rows visible after a run (2026-04-21)
- Demo dataset tooling added: 34-entry manifest, `seed_demo_captures.py`, tests, design spec/plan, and evaluation doc scaffold are now in place (2026-04-21)
- Backend refactor finished functionally; remaining verify gap is still `ruff`/`mypy` availability in this shell (2026-04-21)

### Now

**chore/demo-seed — Demo Dataset + Output Quality**

- [x] Read demo dataset brief and current capture/session patterns
- [x] Write design spec and implementation plan
- [x] Build manifest-driven demo dataset manifest covering current `sakad-backend/test-images/` assets plus placeholders
- [x] Add `scripts/seed_demo_captures.py` with seeding + evaluation output
- [x] Run `python -m pytest tests/ -x -q` (`86 passed`)
- [ ] Run `python scripts/seed_demo_captures.py` in a configured environment and document output quality

**Exit criteria:** live seed completes with Supabase credentials, docs capture actual taxonomy/reference outcomes, and missing placeholder assets are replaced with royalty-free images where needed.

### Next

- Provide `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`, then rerun `python scripts/seed_demo_captures.py`
- Replace the 24 placeholder filenames in `sakad-backend/eval/demo_dataset_manifest.json` with real royalty-free images in `sakad-backend/test-images/`
- Refresh `docs/eval_demo_dataset.md` from the successful seeded run and lock the 3-5 safest live-demo images
- Finish verify gate for `backend-refactor` once `ruff` and `mypy` are available
- Week 3: `GET /api/captures/{id}`, `POST /api/clusters/run` (HDBSCAN), `GET /api/clusters`, `POST /api/generate` (Gemini), share live URL with partner
- Week 4: Deploy to Railway, Supabase Realtime on captures table, `GET /api/sessions/{id}/reflection`
- Week 5: Seed 40+ demo captures, optimize `POST /api/capture` to <3s, full health endpoint, backup demo video

---

## Workflow

| Field     | Value                         |
| --------- | ----------------------------- |
| Command   | /new-feature demo-dataset-quality |
| Phase     | 5 — Verify                    |
| Next step | Provide runtime env, run live seed, and refresh docs from actual output |

### Checklist

- [x] Worktree created (`chore/demo-seed`)
- [x] Project state read
- [x] Plugins verified — Codex environment uses manual equivalent workflow steps
- [x] PRD created — N/A: internal demo dataset/evaluation task
- [x] Research done — brief, routes, scripts, manifests, taxonomy, and test images reviewed
- [x] Brainstorming complete — manifest-driven approach selected over one-off or DB-bypass approaches
- [x] Plan written — `docs/superpowers/plans/2026-04-21-demo-dataset-quality.md`
- [x] Plan review loop (1 iteration) — P1 constraints around UUID session ids and `specs-bucket` handling folded into the plan before implementation
- [x] TDD execution complete
- [x] Code review loop (2 iterations) — reviewer-found P1/P2 issues fixed; no remaining P0/P1/P2 findings in changed files
- [x] Simplified
- [ ] Verified (tests/lint/types) — pytest passed; live seed blocked by missing Supabase env in current shell
- [ ] E2E use cases tested (if user-facing) — N/A: internal seeding/eval tooling
- [ ] Learnings documented (if any)
- [x] State files updated
- [ ] Committed and pushed
- [ ] PR created
- [ ] PR reviews addressed
- [ ] Branch finished

---

## Open Questions

- Whether `specs-bucket` already exists in the target Supabase project, since `/api/capture` itself still uploads to the `captures` bucket
- Whether the current taxonomy/reference corpus is strong enough on abstract/environmental imagery, or if those captures should stay secondary in the live demo mix

## Blockers

- Live seeding is blocked in the current shell because `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are unset

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
