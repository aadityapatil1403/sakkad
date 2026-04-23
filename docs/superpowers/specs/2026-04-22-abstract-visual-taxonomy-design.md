# Abstract Visual Taxonomy Design

## Goal

Extend the canonical taxonomy with 25 `abstract_visual` labels while preserving every existing `fashion_streetwear` entry byte-for-byte, and make taxonomy seeding operate correctly when `data/taxonomy.json` contains more than one domain.

## Constraints

- `data/taxonomy.json` remains the single source of truth.
- Existing `fashion_streetwear` entries must remain unchanged.
- `sakad-backend/scripts/seed_taxonomy.py` must continue to reuse stable IDs when labels already exist.
- Stale-row deletion must be scoped only to domains represented in the canonical file.
- The checked-in migration still excludes `abstract_visual`; live seeding should therefore surface a Supabase constraint failure immediately if the target DB was not updated.

## Options Considered

### 1. Keep single-domain seeding and split taxonomy files

Pros: no seed-script logic change.
Cons: breaks the canonical single-file taxonomy source, adds operational complexity, and conflicts with the requested mixed-domain taxonomy shape.

### 2. Remove the single-domain guard only

Pros: minimal code diff.
Cons: incorrect stale cleanup because it would still fetch and delete rows for only one domain, leaving mixed-domain seeds incomplete. Rejected.

### 3. Treat represented domains as a set throughout the seed flow

Pros: preserves one canonical taxonomy file, keeps `build_row()` unchanged, scopes lookups and stale cleanup correctly, and matches the requested behavior.
Cons: requires modest test updates and broader seed-query coverage.

## Decision

Implement option 3. The seed script will derive the represented domain set from the taxonomy file, fetch existing rows across all represented domains, reuse existing IDs by label, and delete stale rows only inside those same represented domains.

## Verification

- Unit tests cover mixed-domain taxonomy data and mixed-domain seeding behavior.
- Run targeted pytest coverage first.
- Run the live seed script last; if Supabase rejects `abstract_visual`, stop and report that the live DB constraint still needs updating.

## E2E

N/A — backend data and seed tooling only; no user-facing API contract changes.
