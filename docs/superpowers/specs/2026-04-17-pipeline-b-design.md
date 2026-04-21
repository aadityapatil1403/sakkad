# Pipeline B: Semantics-First Classification

**Date:** 2026-04-17  
**Status:** Approved for implementation

---

## Context

The current pipeline (Pipeline A) classifies fashion images using image-only SigLIP embeddings. Gemini-generated layer1/layer2 tags exist but are passengers — they don't influence taxonomy scoring. Image-only was chosen after ablations showed it beat the prior image+text blend (which used raw garment tokens as text input).

Pipeline B tests the hypothesis that **semantic style phrases** ("cowboy core", "sports-luxury streetwear") embed closer to taxonomy labels than raw garment tokens do, because they speak the same language. The eval harness decides whether this hypothesis holds — if image-only still wins, Pipeline A is kept.

---

## Pipeline B Dependency Graph

```
image ──────────────────────────────────────────────── SigLIP ──► image_vec ──────┐
  │                                                                                │
  ├──► Gemini layer1 ──► Gemini layer2 ──► Gemini layer3 ──► SigLIP ──► layer3_vec
  │                                                                                │
  │                                         ┌──────────────────────────────────────┘
  │                                         ▼
  │                               eval_harness_winner(image_vec, layer3_vec)
  │                                         │
  │                                         ▼
  │                                    taxonomy_matches
  │                                         │
  │              ┌──────────────────────────┘
  │              │
  └──────────────┴──► Gemini layer4 (image + taxonomy + layer1 + layer2 + layer3)
                                            │
                                            ▼
                                        references
```

SigLIP image embedding runs **concurrently** with the Gemini chain. Both results meet at taxonomy scoring.

---

## Layer Contracts

| Layer    | Input                                       | Output                                                              | Model             |
| -------- | ------------------------------------------- | ------------------------------------------------------------------- | ----------------- |
| layer1   | image                                       | 10 single-word visual primitives (colors, materials, silhouettes)   | Gemini vision     |
| layer2   | image + layer1                              | 10 hyphenated fashion descriptors (garment constructions, styling)  | Gemini vision     |
| layer3   | image + layer1 + layer2                     | 3–5 style phrases + 1 summary sentence (semantic style translation) | Gemini vision     |
| taxonomy | image_vec + layer3_vec                      | top-5 labels with softmax scores                                    | SigLIP cosine sim |
| layer4   | image + taxonomy + layer1 + layer2 + layer3 | 3–5 designer/era/cultural references                                | Gemini vision     |

### Layer3 Output Format

Semantic style translation — taxonomy-adjacent but not taxonomy-identical. Answers "what kind of fashion styling is this pointing toward?" — more abstract than garment tags, less final than taxonomy prediction.

```json
{
  "style_phrases": [
    "cowboy-core denim styling",
    "heritage rodeo details",
    "bootcut denim silhouette",
    "frontier americana workwear"
  ],
  "style_summary": "A western-inspired denim look with cowboy accessories and heritage rodeo cues."
}
```

**Constraint:** phrases must be taxonomy-adjacent but NOT verbatim taxonomy label names. The rule: if a phrase would match a taxonomy label character-for-character (case-insensitive), it is rejected. Paraphrases and descriptive expansions are allowed — e.g. "cowboy-core denim styling" is fine, "Cowboy Core" is not. This keeps taxonomy scoring as a real vector similarity step rather than a hidden Gemini classification.

**SigLIP input (step 5):** phrases joined with commas + summary sentence as one string:
`"cowboy-core denim styling, western americana, heritage rodeo details, bootcut denim silhouette. A western-inspired denim look with cowboy accessories and heritage rodeo cues."`

### Layer4 Output Format

```json
{
  "references": [
    "Helmut Lang SS99",
    "90s rave culture",
    "Vivienne Westwood punk"
  ]
}
```

---

## Taxonomy Scoring Math

Unchanged from Pipeline A — only the text input changes:

```python
# Pipeline A (current)
text_input = " ".join(layer1_tags + layer2_tags)  # raw garment tokens

# Pipeline B
text_input = ", ".join(layer3_phrases) + ". " + layer3_summary  # phrases + summary sentence

# Scoring (same in both)
text_vec = siglip.encode_text(text_input)
blended  = α * image_vec + (1 - α) * text_vec
blended  = blended / np.linalg.norm(blended)
logits   = 100.0 * (taxonomy_embeddings @ blended)
scores   = softmax(logits)
```

---

## Eval Harness: New Configs

The existing eval harness sweeps ablation configs. Pipeline B adds these alongside existing baselines:

| Config                   | α (image) | β (layer3) | Notes                              |
| ------------------------ | --------- | ---------- | ---------------------------------- |
| `pipeline_b_layer3_only` | 0.0       | 1.0        | Pure semantic test (vision layer3) |
| `pipeline_b_blend_08_02` | 0.8       | 0.2        | Light semantic boost               |
| `pipeline_b_blend_06_04` | 0.6       | 0.4        | Balanced                           |
| `pipeline_b_blend_05_05` | 0.5       | 0.5        | Equal weight                       |

Existing `fashion_image_only` (α=1.0) remains the baseline. Winner = highest top1 hit rate, tiebreak on top3, then mean primary rank.

**Decision rule:** If any Pipeline B config achieves strictly higher top1 hit rate than `fashion_image_only` → ship Pipeline B with the winning α. Ties go to Pipeline A (image-only is simpler and has no extra Gemini latency). Otherwise → keep Pipeline A, layer3/layer4 stored as display-only annotations.

---

## What Changes in the Codebase

### `sakad-backend/services/gemini_service.py`

- Add `get_layer3_tags(image_bytes, layer1, layer2) -> Layer3Response` — vision call, returns `style_phrases` (3–5) + `style_summary` (1 sentence)
- Add `get_layer4_references(image_bytes, taxonomy_matches, layer1, layer2, layer3) -> list[str]` — vision call, returns 3–5 designer/era/cultural references

### `sakad-backend/routes/capture.py`

- Wire layer3 into the pipeline after layer2
- Build layer3 text input as `", ".join(style_phrases) + ". " + style_summary` and pass to SigLIP text encoder for taxonomy scoring
- Call layer4 after taxonomy resolves
- Store layer3 and layer4 in Supabase response

### `sakad-backend/scripts/evaluate_classifier.py`

- Add `layer3` as a new text variant (alongside existing `layer1`, `layer2`, `layer1_layer2`)
- Add 4 new Pipeline B ablation configs to the sweep

---

## What Does NOT Change

- SigLIP model, image encoding, taxonomy scoring math
- Taxonomy labels in Supabase (no re-seeding needed)
- Layer1 and layer2 prompts
- Eval harness metrics (top1, top3, mean primary rank)
- Fallback behavior: if Gemini fails, image-only still works

---

## Verification

1. **Unit:** `gemini_service.py` — test `get_layer3_tags` returns `style_phrases` (3–5 items, not direct taxonomy labels) and `style_summary` (non-empty string)
2. **Unit:** `gemini_service.py` — test `get_layer4_references` returns 3–5 non-empty strings
3. **Integration:** Run eval harness on all 10 manifest images — confirm Pipeline B configs appear in output
4. **Comparison:** Check eval report — does any Pipeline B config top1 hit rate ≥ `fashion_image_only`?
5. **Smoke:** POST one image to `/api/capture` — confirm `layer3`, `layer4`, `taxonomy_matches` all present in response

---

## Decision Gate

| Outcome                        | Action                                                              |
| ------------------------------ | ------------------------------------------------------------------- |
| Pipeline B config wins or ties | Adopt winning α, ship Pipeline B                                    |
| Pipeline A still wins          | Keep image-only taxonomy, keep layer3/layer4 as display annotations |
