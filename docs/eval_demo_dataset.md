# Demo Dataset Evaluation

## Scope

This document tracks the demo corpus used for the Spectacles → web app walkthrough. The source of truth for target captures is `sakad-backend/eval/demo_dataset_manifest.json`.

- Total manifest entries: 25 (10 unique images reused across 3 sessions)
- Available local images: 10
- Demo session aliases: `session_fashion`, `session_abstract`, `session_mixed`
- Latest script run: `2026-04-21`
- Latest run output: `sakad-backend/eval/demo_dataset_last_run.json`

## Evaluation Table

| image                 | expected taxonomy               | actual top match | score  | pass/fail         |
| --------------------- | ------------------------------- | ---------------- | ------ | ----------------- |
| leather_jacket.jpg    | Biker, Moto Culture             | Biker            | 0.1235 | PASS              |
| furcoat.jpg           | Y2K, Club Kid                   | Y2K              | 0.1240 | PASS              |
| old_money.jpg         | Old Money, Preppy               | Preppy           | 0.1481 | PASS              |
| japanjersey.jpg       | Japanese Streetwear, Streetwear | Maximalism       | 0.0511 | PASS (acceptable) |
| monochromatic.jpg     | Monochrome, 90s Minimalism      | Biker            | 0.0471 | PASS (acceptable) |
| western.jpg           | Western Americana, Cowboy Core  | 70s Revival      | 0.0644 | FAIL              |
| vintage.jpg           | Vintage Americana, 70s Revival  | Workwear         | 0.0654 | FAIL              |
| workwear.jpg          | Workwear, Utilitarian           | Biker            | 0.1091 | FAIL              |
| soccer_streetwear.jpg | Streetwear, Sportswear Luxe     | Preppy           | 0.0856 | FAIL              |
| formal_wear.jpg       | Tailoring, Soft Tailoring       | Workwear         | 0.0484 | FAIL              |

## Weak Cases

- `western.jpg`: top match is `70s Revival` — taxonomy labels for Western/Americana need better SigLIP captions. Avoid as lead demo image.
- `vintage.jpg`: top match is `Workwear` — 70s denim silhouette colliding with workwear cues. Avoid.
- `workwear.jpg`: top match is `Biker` — both are heavy-fabric utility aesthetics; label descriptions too similar. Needs caption differentiation.
- `soccer_streetwear.jpg`: top match is `Preppy` — jersey styling being read as preppy. Taxonomy caption gap.
- `formal_wear.jpg`: top match is `Workwear` — structured suit collapsing to workwear. Caption gap between tailoring and workwear labels.
- **Reference scores**: All scores near zero (< 0.10). Reference corpus is too sparse for reliable retrieval. Do not rely on reference_matches for demo until corpus is seeded and re-evaluated.

## Systemic Issues Identified

1. **Taxonomy score magnitude too low** — all top scores < 0.15. Labels need better caption-style descriptions tuned to actual image content.
2. **Reference retrieval near-random** — reference_matches scores ≤ 0.08 indicate corpus is too sparse or captions don't match image embeddings.
3. **Repeated image × session rows produce identical results** — same embedding, so abstract/mixed session rows add no diversity signal in this run.

## Safest Live Demo Images

- `old_money.jpg` — Preppy (0.1481) — most reliable
- `furcoat.jpg` — Y2K (0.1240) — reliable
- `leather_jacket.jpg` — Biker (0.1235) — reliable

Use these three as the showcased captures. Lead with session counts and the visual collage; de-emphasize taxonomy label names until corpus is tuned.

## Next Steps Before Demo

1. Seed reference corpus with 50+ entries: `python scripts/seed_reference_corpus.py`
2. Verify reference scores improve above 0.10 threshold
3. Re-tune taxonomy label captions in `data/taxonomy.json` to differentiate workwear / biker / utilitarian / tailoring
4. Re-run `python scripts/seed_demo_captures.py` after corpus updates to refresh this doc
