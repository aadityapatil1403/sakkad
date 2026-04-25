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

- Built `web/sakkad-showcase/` — full React/Vite showcase UI with upload, pipeline reveal, three-column result (taxonomy/references/reflection), gallery strip, Explore Relationships modal, Sketch Stage placeholder; 18 tests passing, clean build (2026-04-24)
- Created backend showcase UI planning artifacts: PRD, design spec, TDD implementation plan (2026-04-24)

### Now

**Backend Showcase UI**

- [x] Plan a polished Apple-adjacent fashion UI for backend upload/classification demo
- [x] Recommend standalone `web/sakkad-showcase/` React/Vite app
- [x] User approved matching the partner app's relationship-to-sketch flow
- [x] TDD implementation complete — 18 tests, clean build
- [ ] Commit and merge to main

**Week 3 — Demo-readiness and Partner Contract**

- [ ] Run live demo seed (`python scripts/seed_demo_captures.py`) once `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` are set
- [ ] Replace 24 placeholder images in `sakad-backend/eval/demo_dataset_manifest.json` with royalty-free images
- [ ] Ship first-pass clustering: `POST /api/clusters/run`, `GET /api/clusters`
- [x] Improve partner narrative surfaces: `POST /api/generate`, `GET /api/sessions/{id}/reflection`

**Exit criteria:** Partner can consume documented session/capture reads, live seed documents actual taxonomy/reference outcomes, clustering works on seeded demo data.

### Next

- Implement backend showcase UI with TDD, starting with the typed API client and single-image upload flow
- Week 3: `POST /api/clusters/run` (HDBSCAN), `GET /api/clusters`, share live URL with partner
- Week 4: Deploy to Railway, Supabase Realtime on captures table, improve health/readiness endpoints
- Week 5: Seed 40+ demo captures, optimize `POST /api/capture` to <3s, full health endpoint, backup demo video

---

## Workflow

| Field     | Value                                |
| --------- | ------------------------------------ |
| Command   | /new-feature backend-showcase-ui     |
| Phase     | 4 — Execute                          |
| Next step | Scaffold TDD React/Vite showcase app |

### Checklist

- [x] Worktree created
- [x] Project state read
- [x] Plugins verified (Codex manual equivalent)
- [x] PRD created
- [x] Research done
- [x] Design guidance loaded (if UI)
- [x] Brainstorming complete
- [x] Plan written
- [x] Plan review loop (1 iteration) — PASS
- [x] TDD execution complete
- [x] Code review loop (1 iteration) — PASS
- [x] Simplified
- [x] Verified (tests/lint/types)
- [ ] E2E use cases tested (if user-facing)
- [ ] Learnings documented (if any)
- [x] State files updated
- [ ] Committed and pushed
- [ ] PR created
- [ ] PR reviews addressed
- [ ] Branch finished

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
