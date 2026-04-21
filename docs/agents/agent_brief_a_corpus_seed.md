# Agent Brief A — Reference Corpus and Seed

## Mission
Build the MVP reference corpus foundation for designer/reference retrieval. This agent owns the data model, storage plan, and seed path for a small curated demo-quality corpus.

## Product Context
Sakkad is now focused on fashion designers. The next-week MVP goal is not better taxonomy experimentation; it is turning a captured image into useful designer/reference suggestions. The current backend already supports capture, sessions, image embeddings, taxonomy, and palette extraction. What is missing is a curated reference corpus that retrieval can query.

## What You Own
- Reference corpus schema
- Supabase storage/migration for the corpus
- Seed file format and seed script
- A small curated initial dataset for demo retrieval

## What You Must Not Own
- Retrieval ranking logic
- `/api/capture` route integration
- Session/detail read APIs
- Relationship generation

## Recommended Files
- `sakad-backend/migrations/` for the new reference corpus migration
- `sakad-backend/scripts/` for the seed script
- `data/` or `sakad-backend/data/` for the curated seed dataset

## Required Output
Define a reference corpus that supports retrieval. The stored shape should include:
- `id`
- `designer`
- `brand`
- `collection_or_era`
- `title`
- `description`
- `taxonomy_tags` or equivalent structured tags
- `image_url` nullable
- `embedding`
- optional `metadata` JSON

The dataset should be:
- intentionally small
- manually curated
- high quality for the demo
- fashion-designer relevant

## Implementation Requirements
- Use Supabase as the source of truth for the reference corpus.
- Seed descriptions should be embedded using the same SigLIP text path the backend already uses for taxonomy.
- Keep the seed path reproducible.
- Favor clarity over scale; do not build a broad ingestion pipeline.

## Deliverables
- migration for the reference corpus table
- curated seed dataset
- seed script that populates the table with embeddings
- short note in code/comments or README-level context if the seed format is non-obvious

## Test / Validation
- seeding runs successfully against the target schema
- embeddings are persisted
- seeded rows are queryable by later services
- failure modes are clear if environment variables or required fields are missing

## Handoff Contract
When done, Agent B should be able to rely on:
- the exact table/field names
- the exact embedding field format
- the exact seed shape

Do not change route code. Keep this workstream data-only plus seed plumbing.
