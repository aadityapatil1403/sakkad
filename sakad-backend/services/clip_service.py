import ast
import io
import os
import threading

from PIL import Image
import torch
import open_clip
import numpy as np
from transformers import AutoProcessor

from config import settings
from services.supabase_client import supabase

os.environ.setdefault("HF_HUB_OFFLINE", "1")

_model = None
_processor = None
_loaded = False  # True only after both _model and _processor are fully assigned
_load_lock = threading.Lock()
_taxonomy_cache: list[dict] | None = None

DOMAIN_CAPS: dict[str, int] = {
    "fashion_streetwear": 3,
    "_default": 1,
}


def _load() -> None:
    global _model, _processor, _loaded
    if _loaded:
        return
    with _load_lock:
        if _loaded:  # double-checked locking — guard on _loaded, not _model
            return
        # open_clip handles marqo-fashionSigLIP weights correctly; AutoModel.from_pretrained
        # fails with torch 2.x due to meta-tensor incompatibility in the custom __init__.
        _model, _, _ = open_clip.create_model_and_transforms(
            f"hf-hub:{settings.CLIP_MODEL_NAME}"
        )
        # AutoProcessor provides the correct T5-based tokenizer and SigLIP image processor
        _processor = AutoProcessor.from_pretrained(
            settings.CLIP_MODEL_NAME,
            trust_remote_code=True,
            local_files_only=True,
        )
        _model.eval()
        _loaded = True  # set last — only visible to other threads once both globals are ready


def get_image_embedding(image_bytes: bytes) -> list[float]:
    _load()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = _processor(images=image, return_tensors="pt")
    with torch.no_grad():
        # normalize=True is required for correct cosine similarity scores with marqo-fashionSigLIP
        image_embeds = _model.encode_image(inputs["pixel_values"], normalize=True)
    return image_embeds.reshape(-1).tolist()


def get_text_embedding(text: str) -> list[float]:
    _load()
    inputs = _processor(text=[text], return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        # normalize=True is required for correct cosine similarity scores with marqo-fashionSigLIP
        text_embeds = _model.encode_text(inputs["input_ids"], normalize=True)
    return text_embeds.reshape(-1).tolist()


def _load_taxonomy() -> list[dict]:
    global _taxonomy_cache
    if _taxonomy_cache is not None:
        return _taxonomy_cache
    response = (
        supabase.table("taxonomy")
        .select("id, label, domain, embedding, embedding_model")
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise RuntimeError(
            "Taxonomy is empty. Run sakad-backend/scripts/seed_taxonomy.py."
        )

    parsed: list[dict] = []
    for row in rows:
        raw = row.get("embedding")
        if raw is None:
            continue
        embedding_model = row.get("embedding_model")
        if embedding_model != settings.TAXONOMY_EMBEDDING_MODEL:
            raise RuntimeError(
                "Taxonomy embeddings were seeded with a different model. "
                "Re-run sakad-backend/scripts/seed_taxonomy.py before serving captures."
            )
        embedding = ast.literal_eval(raw) if isinstance(raw, str) else raw
        parsed.append({
            "id": row["id"],
            "label": row["label"],
            "domain": row["domain"],
            "embedding": np.array(embedding, dtype=np.float32),
        })

    if not parsed:
        raise RuntimeError(
            "Taxonomy rows are missing embeddings. "
            "Run sakad-backend/scripts/seed_taxonomy.py."
        )
    _taxonomy_cache = parsed
    return _taxonomy_cache


def _score_all(image_embedding: list[float], taxonomy: list[dict]) -> dict[str, float]:
    image_vector = np.array(image_embedding, dtype=np.float32)
    score_pairs = [
        (row["label"], round(float(row["embedding"] @ image_vector), 4))
        for row in taxonomy
    ]
    score_pairs.sort(key=lambda item: item[1], reverse=True)
    return dict(score_pairs)


def classify(image_embedding: list[float]) -> dict[str, float]:
    taxonomy = _load_taxonomy()
    if not taxonomy:
        raise RuntimeError("Taxonomy is empty.")

    scores = _score_all(image_embedding, taxonomy)
    domains = {row["domain"] for row in taxonomy}
    if len(domains) == 1:
        return dict(list(scores.items())[:5])

    capped_results: list[tuple[str, float]] = []
    for domain in sorted(domains):
        domain_rows = [
            (row["label"], scores[row["label"]])
            for row in taxonomy
            if row["domain"] == domain
        ]
        domain_rows.sort(key=lambda item: item[1], reverse=True)
        cap = DOMAIN_CAPS.get(domain, DOMAIN_CAPS["_default"])
        capped_results.extend(domain_rows[:cap])

    capped_results.sort(key=lambda item: item[1], reverse=True)
    return dict(capped_results)
