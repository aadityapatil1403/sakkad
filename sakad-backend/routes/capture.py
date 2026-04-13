import ast
import io
import uuid

import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from services.clip_service import get_image_embedding
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


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _classify(image_embedding: list[float]) -> list[dict]:
    taxonomy = _load_taxonomy()
    img_vec = np.array(image_embedding, dtype=np.float32)
    scored = [
        {
            "id": row["id"],
            "label": row["label"],
            "domain": row["domain"],
            "score": round(_cosine_similarity(img_vec, row["embedding"]), 4),
        }
        for row in taxonomy
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:5]


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

    filename = f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'jpg'}"

    storage_response = supabase.storage.from_(STORAGE_BUCKET).upload(
        path=filename,
        file=image_bytes,
        file_options={"content-type": file.content_type or "image/jpeg"},
    )
    if hasattr(storage_response, "error") and storage_response.error:
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {storage_response.error}")

    public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

    embedding = get_image_embedding(image_bytes)
    taxonomy_matches = _classify(embedding)
    palette = _extract_palette(image_bytes)

    insert_response = supabase.table("captures").insert({
        "image_url": public_url,
        "embedding": embedding,
        "taxonomy_matches": taxonomy_matches,
        "tags": {"palette": palette},
    }).execute()

    if not insert_response.data:
        raise HTTPException(status_code=500, detail="Failed to insert capture record")

    return insert_response.data[0]
