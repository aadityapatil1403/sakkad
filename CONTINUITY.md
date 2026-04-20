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

- `CLAUDE.md` updated to match the current Sakkad product story, ownership split, backend status, demo shape, and near-term milestones (2026-04-20)
- `AGENTS.md` written — compact harness guide for Codex covering workflow decision matrix, skills→equivalents, quality gates, hooks, coding standards, state file rules (2026-04-18)
- End-to-end pipeline smoke test: all 5 test images processed successfully (furcoat, japanjersey, western, workwear, leather_jacket) — layer1/layer2 tags, taxonomy_matches, palette all returning (2026-04-16)

### Now

**Week 2 — Backend Core**

- [ ] Sessions API: `POST /api/sessions/start`, `POST /api/sessions/{id}/end`, `GET /api/sessions`
- [ ] Seed 15+ fashion images to validate classification output
- [x] Classification: cosine sim on capture embedding → top 5 taxonomy matches → store in `taxonomy_matches`
- [x] Color palette: PIL KMeans k=5 → hex array → store in `tags.palette`
- [x] Gemini layer1/layer2 tags: 10 single-word + 10 hyphenated descriptors, blended into taxonomy scoring

**Exit criteria:** Sessions API live.

### Next

- Week 3: `GET /api/sessions/{id}`, `GET /api/captures/{id}`, `POST /api/clusters/run` (HDBSCAN), `GET /api/clusters`, `POST /api/generate` (Gemini), `API_CONTRACT.md`, seed 30+ demo captures, share live URL with partner
- Week 4: Deploy to Railway, Supabase Realtime on captures table, `GET /api/sessions/{id}/reflection` (Gemini 3-sentence insight), add optional capture fields (session_id, location, weather_data)
- Week 5: Seed 40+ demo captures, optimize `POST /api/capture` to <3s, `GET /api/health` full status, record backup demo video

---

## Workflow

| Field     | Value |
| --------- | ----- |
| Command   | none  |
| Phase     | —     |
| Next step | —     |

---

## Open Questions

- `leather_jacket.jpg` layer2 tags return null — Gemini returned tags that failed `t.count("-") == 1` validator; investigate what was returned
- Taxonomy accuracy questionable: `western.jpg` → "Tropical", `furcoat.jpg` → "Y2K" are poor matches — may need taxonomy embedding tuning

## Blockers

- None currently

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
