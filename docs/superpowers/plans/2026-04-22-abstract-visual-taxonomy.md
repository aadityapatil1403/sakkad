# Abstract Visual Taxonomy Implementation Plan

## Scope

Add 25 `abstract_visual` taxonomy entries, update mixed-domain taxonomy seeding, expand unit tests, and record the change in the changelog.

## Steps

1. Make taxonomy/seed tests fail for the new mixed-domain expectation.
   Verification: `python -m pytest tests/test_seed_taxonomy.py tests/test_taxonomy_data.py` fails for the expected reasons.

2. Update `data/taxonomy.json` with exactly 25 new `abstract_visual` entries.
   Verification: taxonomy data test asserts both represented domains and an `abstract_visual` count of 25.

3. Refactor `scripts/seed_taxonomy.py` to seed across all represented domains.
   Verification: unit tests prove multi-domain fetch, ID reuse, and stale deletion behavior.

4. Update `docs/CHANGELOG.md` for the significant multi-file change.
   Verification: changelog entry reflects the taxonomy expansion and mixed-domain seed support.

5. Run verification.
   Verification:
   - `python -m pytest tests/test_seed_taxonomy.py tests/test_taxonomy_data.py`
   - `python scripts/seed_taxonomy.py`

## Review Notes

- Keep `build_row()` and `on_conflict="label"` unchanged unless live seeding proves otherwise.
- Do not modify existing `fashion_streetwear` taxonomy entries.
- Treat Supabase domain-constraint failure during the live seed as a legitimate environment blocker, not a code bug.

## E2E

N/A — no user-facing API flow changes.
