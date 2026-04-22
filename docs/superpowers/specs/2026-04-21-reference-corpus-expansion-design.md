# Reference Corpus Expansion Design

Date: 2026-04-21

## Goal

Expand the canonical designer reference corpus from a small mixed set to a 50+ entry fashion-reference library covering:

- western/americana
- workwear/utility
- biker/moto
- japanese streetwear
- minimalism/tailoring
- avant-garde

Each entry must include `brand`, `designer`, `title`, `description`, and `collection_or_era`, with descriptions written densely enough to anchor SigLIP text embeddings.

## Relevant Code

- `data/reference_corpus.json`
- `sakad-backend/scripts/seed_reference_corpus.py`
- `sakad-backend/tests/test_reference_corpus_data.py`
- `sakad-backend/tests/test_seed_reference_corpus.py`

## Approaches Considered

### 1. Put all references directly in the seed script

Pros:
- Single file to edit

Cons:
- Breaks the existing canonical-data contract
- Harder to review and reuse outside the script
- Makes tests more awkward

### 2. Keep canonical JSON, expand schema lightly with bucket metadata

Pros:
- Preserves the existing data-driven seed flow
- Makes corpus review easy
- Lets embeddings carry coarse bucket context without changing required fields

Cons:
- Requires test updates and slightly richer metadata

### 3. Split corpus into one file per bucket

Pros:
- Cleaner authoring by category

Cons:
- Adds loader complexity and more moving parts
- Unnecessary for the current corpus size

## Recommendation

Use approach 2.

Keep `data/reference_corpus.json` as the single canonical source, expand it to 54 entries, add `metadata.bucket` to every record, and include the bucket in `build_embedding_text()` so the seeded embeddings preserve coarse aesthetic grouping while still prioritizing specific silhouette, fabric, construction, and mood language.

## Acceptance Criteria

- Canonical corpus contains at least 50 entries
- All six requested buckets are present
- Every bucket has at least 8 entries
- Seed script includes bucket context in embedding text when provided
- Corpus tests and seed-script tests pass
