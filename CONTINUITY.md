# CONTINUITY

## Goal

Build the Sakkad backend (FastAPI + SigLIP + Supabase) so Snap Spectacles can capture fashion inspiration, classify it against a 100-label taxonomy, and surface clusters on a partner-built web app — live demo in 4 weeks.

## Key Decisions

| Decision | Choice | Why |
| -------- | ------ | --- |
| Vision model | SigLIP (`google/siglip-base-patch16-224`) | Sigmoid loss scores each label independently — essential for multi-aesthetic images |
| Taxonomy size | ~100 labels across 3 tiers | Fashion/Streetwear (~50), Visual/Environmental (~30), Visual Art/Reference (~20) |
| Auth | DEV_USER_ID hardcoded | MVP speed — Supabase Auth only post-demo if time allows |
| Deploy | Railway $5/mo 8GB RAM | SigLIP is 813MB; needs RAM headroom |
| Gemini | Backend-proxied only | No API keys exposed to Lens Studio or web frontend |
| Clustering | HDBSCAN on SigLIP embeddings | Density-based, no fixed k — better for fashion aesthetic clusters |

---

## State

### Done (recent)

- POST /api/capture — image → Supabase Storage → SigLIP embedding → captures row (2026-04-07)
- GET /api/gallery — returns rows with image_url and embedding (2026-04-07)
- SigLIP model working locally, lazy-loaded (2026-04-07)
- Sessions table schema created in Supabase (2026-04-07)

### Now

**Week 2 — Backend Core**

- [ ] Sessions API: `POST /api/sessions/start`, `POST /api/sessions/{id}/end`, `GET /api/sessions`
- [ ] Build `taxonomy.json` — ~100 fashion labels with visually specific descriptions
- [ ] Seed taxonomy: SigLIP text embeddings → upsert all rows to `taxonomy` table
- [ ] Classification: cosine sim on capture embedding → top 5 taxonomy matches → store in `taxonomy_matches`
- [ ] Color palette: PIL KMeans k=5 → hex array → store in `tags.palette`
- [ ] Seed 15+ fashion images to validate classification output

**Exit criteria:** `POST /api/capture` returns real `taxonomy_matches`. Sessions API live.

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

### Checklist

<!-- Populated when /new-feature or /fix-bug starts -->

---

## Open Questions

- Does `taxonomy_matches` column exist in captures table, or does it need to be added?
- Confirm Supabase pgvector dimension for SigLIP embeddings (should be 768)

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
