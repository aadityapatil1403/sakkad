# Changelog

All notable changes to Sakkad will be documented in this file.

## [Unreleased]

### Added

- Initial project setup with Claude Code configuration
- **2026-04-14** — `services/gemini_service.py`: Gemini Flash 2.0 vision tagging — `get_layer1_tags()` returns 10 single-word visual descriptors, `get_layer2_tags()` returns 10 hyphenated two-word fashion descriptors; non-fatal (returns `[]` on any error)
- **2026-04-14** — `routes/capture.py`: Blended classification — layer1+2 tags joined into text embedding, blended 60% image / 40% text before taxonomy classification; `layer1_tags` and `layer2_tags` stored in captures table
- **2026-04-14** — `config.py`: Added `GEMINI_API_KEY` setting; `requirements.txt`: added `google-genai`

### Changed

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

### Removed

---

## Format

Each entry should include:

- Date (YYYY-MM-DD)
- Brief description
- Related issue/PR if applicable
