# Changelog

All notable changes to Sakkad will be documented in this file.

## [Unreleased]

### Added

- Initial project setup with Claude Code configuration
- **2026-04-18** — `AGENTS.md`: Added Codex harness guide — workflow decision matrix, skills→manual equivalents, quality gates, hook awareness, coding standards, session checklists; designed as permanent AGENTS.md system prompt so Codex follows the same workflow discipline as Claude
- **2026-04-14** — `services/gemini_service.py`: Gemini Flash 2.0 vision tagging — `get_layer1_tags()` returns 10 single-word visual descriptors, `get_layer2_tags()` returns 10 hyphenated two-word fashion descriptors; non-fatal (returns `[]` on any error)
- **2026-04-14** — `routes/capture.py`: Blended classification — layer1+2 tags joined into text embedding, blended 60% image / 40% text before taxonomy classification; `layer1_tags` and `layer2_tags` stored in captures table
- **2026-04-14** — `config.py`: Added `GEMINI_API_KEY` setting; `requirements.txt`: added `google-genai`

### Changed

- **2026-04-21** — `sakad-backend/routes/capture.py`, `services/clip_service.py`, `services/color_service.py`, `services/enrich_service.py`: Refactored capture processing into focused services; classification now returns domain-capped `taxonomy_matches` as `Record<string, number>` and the route is reduced to upload + insert orchestration
- **2026-04-21** — `sakad-backend/tests/test_capture_classify.py`, `test_clip_classify.py`, `test_color_service.py`, `test_enrich_service.py`, `test_sessions_api.py`: Migrated tests to the new service boundaries and dict-shaped taxonomy contract
- **2026-04-21** — `sakad-backend/scripts/evaluate_classifier.py`, `smoke_capture.sh`, `verify_capture_eval.sh`: Updated evaluation/smoke tooling to match cosine-similarity classification without softmax and dict-shaped taxonomy output
- **2026-04-21** — `README.md`, `API_CONTRACT.md`, `docs/agents/`, `docs/planning/`, `docs/worktree/`, `docs/scripts/`: Reorganized repo markdown/docs and added top-level backend run/contract documentation
- **2026-04-13** — Canonicalized taxonomy to `data/taxonomy.json` (100 entries) as single source of truth; deleted stale `sakad-backend/data/taxonomy.json` (94 entries)
- **2026-04-13** — Reformatted all 100 taxonomy descriptions to SigLIP caption style (fashion_streetwear, art_reference, visual_context domains)
- **2026-04-13** — Updated `seed_taxonomy.py` path to load from repo-root `data/taxonomy.json`

- **2026-04-17** — `sakad-backend/tests/test_capture_classify.py`, `test_gemini_service.py`: Updated tests to match current service contracts and classification pipeline
- **2026-04-17** — `sakad-backend/tests/test_seed_taxonomy.py`, `test_taxonomy_data.py`: Added taxonomy seeding and data validation tests
- **2026-04-17** — `sakad-backend/eval/`: Added evaluation harness for classifier accuracy
- **2026-04-17** — `sakad-backend/models/`: Added model layer (likely Pydantic schemas for sessions/captures)
- **2026-04-17** — `sakad-backend/scripts/evaluate_classifier.py`, `smoke_capture.sh`, `verify_capture_eval.sh`: Added evaluation and smoke test scripts
- **2026-04-17** — `sakad-backend/test-images/`: Added 9 test images for classifier evaluation (formal_wear, furcoat, japanjersey, monochromatic, old_money, soccer_streetwear, vintage, western, workwear)
- **2026-04-17** — `data/taxonomy.json`: Updated taxonomy data
- **2026-04-17** — `sakad-backend/migrations/002_taxonomy_domain_constraint.sql`, `README.md`: Added domain constraint migration and updated migration docs
- **2026-04-17** — `sakad-backend/services/gemini_service.py`: Updates to Gemini service (layer1/layer2 tagging refinements)
- **2026-04-17** — `sakad-backend/routes/capture.py`, `scripts/seed_taxonomy.py`: Route and seeding script updates

### Fixed

- **2026-04-21** — `sakad-backend/routes/sessions.py`: session-detail reads now degrade to empty captures when legacy databases are missing `captures.session_id`, matching the write-path compatibility behavior
- **2026-04-21** — `sakad-backend/services/retrieval_service.py`: transient `reference_corpus` load failures no longer disable retrieval for the life of the process; only confirmed schema-missing errors are cached as unavailable
- **2026-04-21** — `sakad-backend/scripts/seed_reference_corpus.py`: stale reference rows are deleted only after successful upserts, preventing partial data loss on failed seed runs

### Removed

---

## Format

Each entry should include:

- Date (YYYY-MM-DD)
- Brief description
- Related issue/PR if applicable
