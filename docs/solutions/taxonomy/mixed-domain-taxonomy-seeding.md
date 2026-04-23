# Problem: Mixed-domain taxonomy seeds were rejected or partially cleaned up

`data/taxonomy.json` moved beyond a single-domain file, but `scripts/seed_taxonomy.py` still enforced exactly one domain and scoped stale-row cleanup to one domain only.

# Root Cause: Seed lookup and cleanup logic assumed one canonical domain

The old seed flow derived one `seed_domain`, fetched existing rows only for that domain, and deleted stale rows only inside that same domain. Removing the guard alone would still leave mixed-domain stale cleanup incomplete.

# Solution: Treat represented taxonomy domains as a set across the whole seed flow

Use `get_seed_domains()` to derive all domains present in the canonical taxonomy file, fetch existing rows with `.in_("domain", sorted(domains))`, reuse IDs by label across that represented set, and delete stale rows only within those represented domains.

# Prevention: Keep mixed-domain tests around lookup and stale cleanup

`tests/test_seed_taxonomy.py` now asserts mixed-domain acceptance, multi-domain existing-row fetches, and stale deletion scoped to the represented domain set. `tests/test_taxonomy_data.py` also asserts the canonical `abstract_visual` count.
