# Migrations

Run files in order by numeric prefix in the **Supabase SQL Editor**.

Never auto-run these from application code.

## Files

- `001_classification_columns.sql` — adds nullable JSONB classification columns to `captures` for the 4-layer taxonomy pipeline (`tags`, `taxonomy_matches`, `layer1_tags`–`layer4_tags`)
- `002_taxonomy_domain_constraint.sql` — legacy migration that broadened the `taxonomy.domain` check constraint for an older mixed-domain taxonomy. The current canonical `data/taxonomy.json` is fashion-only, so re-seeding now writes only `fashion_streetwear` rows.
- `003_reference_corpus.sql` — creates `reference_corpus` for curated designer references. Contract: `id` is the seed/upsert key, `embedding` is stored as a JSON array of SigLIP float values, and the canonical seed file is `data/reference_corpus.json`.
- `004_taxonomy_embedding_model.sql` — adds `taxonomy.embedding_model` so runtime classification can reject stale embeddings after a CLIP/SigLIP model change. Re-run `sakad-backend/scripts/seed_taxonomy.py` after applying it.
- `005_capture_enrichment_columns.sql` — adds nullable capture enrichment fields used by the demo read path (`session_id`, `reference_matches`, `reference_explanation`)
