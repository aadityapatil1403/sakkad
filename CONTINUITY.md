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

- API contract normalized for read surfaces: `GET /api/gallery` and `GET /api/sessions/{id}` now share one capture serializer, `GET /api/captures/{id}` was added, and backend-local `sakad-backend/API_CONTRACT.md` now documents the stable partner contract (2026-04-21)
- Backend refactor completed and verified with pytest; follow-up work is now focused on stable read contracts for partner consumption (2026-04-21)

### Now

**feat/api-contract — Read Contract Normalization**

- [x] Audit `GET /api/gallery`, `GET /api/sessions`, `GET /api/sessions/{id}` against the required capture shape
- [x] Add `GET /api/captures/{id}` and normalize capture read payloads
- [x] Write backend-local `API_CONTRACT.md` and finish targeted test coverage

**Exit criteria:** complete for pytest-scoped verification; full lint/type verification still depends on local tooling availability.

### Next

- Week 3: `POST /api/clusters/run` (HDBSCAN), `GET /api/clusters`, `POST /api/generate` (Gemini), seed 30+ demo captures, share live URL with partner
- Week 4: Deploy to Railway, Supabase Realtime on captures table, `GET /api/sessions/{id}/reflection`
- Week 5: Seed 40+ demo captures, optimize `POST /api/capture` to <3s, full health endpoint, backup demo video

---

## Workflow

| Field     | Value                         |
| --------- | ----------------------------- |
| Command   | /new-feature api-contract |
| Phase     | 5 — Verify |
| Next step | Provision `ruff` and `mypy` if full verify gate is needed before commit |

### Checklist

- [x] Worktree created (`feature/api-contract`)
- [x] Project state read
- [x] Plugins verified
- [x] PRD created — N/A: direct partner contract task from brief
- [x] Research done — audited route/test surface and brief requirements for read endpoints
- [x] Brainstorming complete — normalize reads through one shared capture serializer instead of per-route ad hoc shapes
- [x] Plan written — `docs/superpowers/plans/2026-04-21-api-contract.md`
- [x] Plan review loop (1 iteration) — PASS
- [x] TDD execution complete
- [x] Code review loop (1 iteration) — no remaining P0/P1/P2 findings in changed files
- [x] Simplified
- [ ] Verified (tests/lint/types) — pytest passed; `ruff` and `mypy` unavailable in current shell
- [x] E2E use cases tested — API happy path and `404` path covered for capture detail
- [ ] Learnings documented (if any)
- [x] State files updated
- [ ] Committed and pushed
- [ ] PR created
- [ ] PR reviews addressed
- [ ] Branch finished

---

## Open Questions

- Whether `GET /api/sessions` should eventually gain preview metadata for the web app, or remain a pure session list while detail routes own capture reads

## Blockers

- `ruff` and `mypy` are not installed in the current shell environment, so the full verify gate still cannot complete once implementation is done

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
