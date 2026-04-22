# Problem: Reference corpus seed fails with `invalid input syntax for type uuid`

## Root Cause

The `reference_corpus.id` column in Supabase is typed as `uuid`, but the expanded corpus was temporarily authored with slug-style string IDs. Unit tests only checked that `id` was a non-empty string, so the incompatibility was not caught until the live upsert.

## Solution

Keep corpus IDs as UUID strings in `data/reference_corpus.json`. Add a regression test in `sakad-backend/tests/test_reference_corpus_data.py` that parses every `id` with `UUID(...)`.

## Prevention

- Treat seed-data primary keys as part of the database contract, not just content metadata.
- When expanding canonical JSON seed files, mirror the live column type in data tests.
