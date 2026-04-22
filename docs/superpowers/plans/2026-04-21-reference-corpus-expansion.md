# Reference Corpus Expansion Plan

Date: 2026-04-21

1. Tighten corpus tests to require a 50+ reference set and explicit bucket metadata.
2. Add a failing seed-script test requiring bucket context in the embedding text.
3. Replace `data/reference_corpus.json` with a 54-entry canonical dataset spanning the six requested buckets.
4. Update `seed_reference_corpus.py` to include bucket context in `build_embedding_text()`.
5. Run focused tests for corpus data and seed logic.
6. Run the Supabase seeding command and record whether the current environment is configured to complete it.
