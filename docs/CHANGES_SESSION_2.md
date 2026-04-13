# Session 2 Changes

## Model: google/siglip-base-patch16-224 → Marqo/marqo-fashionSigLIP

The vision-language model was swapped to one purpose-built for fashion retrieval.

**Why:** marqo-fashionSigLIP was trained specifically on fashion image-text pairs. It produces better
cosine similarity scores between fashion images and aesthetic labels than the generic SigLIP base.

**How it loads:**

- Weights loaded via `open_clip.create_model_and_transforms("hf-hub:Marqo/marqo-fashionSigLIP")`
- Tokenization and image preprocessing via `AutoProcessor` (T5 tokenizer + SigLIP image processor)
- `AutoModel.from_pretrained` was tried first but fails on torch 2.x due to a meta-tensor
  incompatibility in the model's custom `__init__`; open_clip loads correctly

**Embedding behavior:**

- Shape: `[1, 768]` — same dimension as before, compatible with existing pgvector column
- `normalize=True` on both `encode_image` and `encode_text` — embeddings are L2-normalized
  (norm = 1.0), so cosine similarity = dot product (required for pgvector `<=>` queries)
- Cached locally at `~/.cache/huggingface/hub/models--Marqo--marqo-fashionSigLIP` (~1.5 GB)
- `HF_HUB_OFFLINE=1` is set at runtime so the model never phones home after initial download

**Files changed:**

- `sakad-backend/services/clip_service.py` — rewritten to use open_clip + AutoProcessor
- `sakad-backend/config.py` — default `CLIP_MODEL_NAME` = `Marqo/marqo-fashionSigLIP`
- `sakad-backend/.env.example` — updated to match
- `sakad-backend/requirements.txt` — added `open-clip-torch`, `ftfy`

---

## Taxonomy: canonicalized to repo root, reformatted descriptions

**Single source of truth:** `data/taxonomy.json` (100 entries) at repo root is now canonical.
`sakad-backend/data/taxonomy.json` (stale 94-entry copy) was deleted.

**Seed script path updated:** `sakad-backend/scripts/seed_taxonomy.py` now loads from
`../../data/taxonomy.json` (repo root) via `Path(__file__).parent.parent.parent`.

**Description format:** All 100 descriptions reformatted to SigLIP caption style for better
embedding alignment:

- `fashion_streetwear`: `"a photo of someone wearing [Label], [details]..."`
- `art_reference`: `"a photo showing [Label] aesthetic, characterized by [details]..."`
- `visual_context`: `"a photo showing [Label] context, where [details]..."`

**Taxonomy re-seeded** with marqo-fashionSigLIP embeddings: 100/100 rows upserted.

---

## Migrations added

All in `sakad-backend/migrations/` — run manually in Supabase SQL Editor in order.

| File                                 | What it does                                                                                                |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| `001_classification_columns.sql`     | Adds nullable JSONB columns to `captures`: `tags`, `taxonomy_matches`, `layer1_tags`–`layer4_tags`          |
| `002_taxonomy_domain_constraint.sql` | Updates `taxonomy.domain` check constraint to allow `fashion_streetwear`, `art_reference`, `visual_context` |

---

## State after this session

- Taxonomy: 100 entries seeded in Supabase with marqo-fashionSigLIP embeddings
- Model: marqo-fashionSigLIP active on main
- DB: migration 002 applied, taxonomy table truncated and re-seeded
- Migration 001 (`captures` classification columns): **still needs to be run in Supabase**
