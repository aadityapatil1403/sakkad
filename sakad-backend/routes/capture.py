import ast
import asyncio
import functools
import io
import uuid

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from services.clip_service import get_image_embedding, get_text_embedding
from services.gemini_service import get_layer1_tags, get_layer2_tags
from services.supabase_client import supabase

router = APIRouter()

STORAGE_BUCKET = "captures"

# Module-level taxonomy cache: populated on first request
_taxonomy_cache: list[dict] | None = None


def _load_taxonomy() -> list[dict]:
    global _taxonomy_cache
    if _taxonomy_cache is not None:
        return _taxonomy_cache
    response = supabase.table("taxonomy").select("id, label, domain, embedding").execute()
    rows = response.data or []
    parsed = []
    for row in rows:
        raw = row.get("embedding")
        if raw is None:
            continue
        embedding = ast.literal_eval(raw) if isinstance(raw, str) else raw
        parsed.append({
            "id": row["id"],
            "label": row["label"],
            "domain": row["domain"],
            "embedding": np.array(embedding, dtype=np.float32),
        })
    _taxonomy_cache = parsed
    return _taxonomy_cache


def _classify(
    image_embedding: list[float],
    text_embedding: list[float] | None,
) -> list[dict]:
    taxonomy = _load_taxonomy()
    img_vec = np.array(image_embedding, dtype=np.float32)  # (768,) already normalized

    if text_embedding is not None:
        txt_vec = np.array(text_embedding, dtype=np.float32)
        blended = 0.6 * img_vec + 0.4 * txt_vec
        norm = np.linalg.norm(blended)
        blended = blended / norm if norm > 0 else img_vec
    else:
        blended = img_vec

    text_matrix = np.stack([r["embedding"] for r in taxonomy])  # (N, 768)
    logits = 100.0 * (text_matrix @ blended)
    exp = np.exp(logits - logits.max())
    probs = exp / exp.sum()
    k = min(5, len(taxonomy))
    top_idx = np.argsort(probs)[::-1][:k]
    return [
        {
            "id": taxonomy[i]["id"],
            "label": taxonomy[i]["label"],
            "domain": taxonomy[i]["domain"],
            "score": round(float(probs[i]), 4),
        }
        for i in top_idx
    ]


def _kmeans_numpy(pixels: np.ndarray, k: int = 5, max_iter: int = 20) -> np.ndarray:
    """Minimal k-means using numpy — avoids sklearn dependency."""
    rng = np.random.default_rng(0)
    centroids = pixels[rng.choice(len(pixels), k, replace=False)]
    for _ in range(max_iter):
        dists = np.linalg.norm(pixels[:, None] - centroids[None], axis=2)
        labels = np.argmin(dists, axis=1)
        new_centroids = np.array([
            pixels[labels == i].mean(axis=0) if np.any(labels == i) else centroids[i]
            for i in range(k)
        ])
        if np.allclose(centroids, new_centroids, atol=1.0):
            break
        centroids = new_centroids
    return centroids


def _extract_palette(image_bytes: bytes) -> list[str]:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((150, 150))
    pixels = np.array(image).reshape(-1, 3).astype(np.float32)
    centroids = _kmeans_numpy(pixels)
    return [f"#{int(round(r)):02x}{int(round(g)):02x}{int(round(b)):02x}" for r, g, b in centroids]


@router.post("/api/capture")
async def capture(file: UploadFile = File(...)) -> dict:
    image_bytes = await file.read()

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"

    storage_response = supabase.storage.from_(STORAGE_BUCKET).upload(
        path=filename,
        file=image_bytes,
        file_options={"content-type": file.content_type or "image/jpeg"},
    )
    if hasattr(storage_response, "error") and storage_response.error:
        raise HTTPException(
            status_code=500,
            detail=f"Storage upload failed: {storage_response.error}",
        )

    public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

    loop = asyncio.get_running_loop()
    image_embedding = await loop.run_in_executor(None, get_image_embedding, image_bytes)

    layer1_fn = functools.partial(get_layer1_tags, image_bytes, mime_type=file.content_type or "image/jpeg")
    layer1 = await loop.run_in_executor(None, layer1_fn)

    if layer1:
        layer2_fn = functools.partial(get_layer2_tags, image_bytes, layer1, mime_type=file.content_type or "image/jpeg")
        layer2 = await loop.run_in_executor(None, layer2_fn)
    else:
        layer2: list[str] = []

    if layer1 or layer2:
        enriched_text = " ".join(layer1 + layer2)
        text_embedding: list[float] | None = await loop.run_in_executor(
            None, get_text_embedding, enriched_text
        )
    else:
        text_embedding = None

    taxonomy_matches = _classify(image_embedding, text_embedding)
    palette = _extract_palette(image_bytes)

    insert_response = supabase.table("captures").insert({
        "image_url": public_url,
        "embedding": image_embedding,
        "taxonomy_matches": taxonomy_matches,
        "layer1_tags": layer1 or None,
        "layer2_tags": layer2 or None,
        "tags": {"palette": palette},
    }).execute()

    if not insert_response.data:
        raise HTTPException(status_code=500, detail="Failed to insert capture record")

    return insert_response.data[0]
