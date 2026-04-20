import ast
import asyncio
import functools
import io
import logging
import uuid

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image

from config import settings
from services.clip_service import get_image_embedding, get_text_embedding
from services.gemini_service import get_layer1_tags_with_model, get_layer2_tags_with_model
from services.retrieval_service import get_reference_matches
from services.supabase_client import supabase

router = APIRouter()
logger = logging.getLogger(__name__)

STORAGE_BUCKET = "captures"
CLASSIFICATION_DOMAIN = "fashion_streetwear"
REFERENCE_CORPUS_TABLE = "reference_corpus"
IMAGE_WEIGHT = 1.0
TEXT_WEIGHT = 0.0

_taxonomy_cache: list[dict] | None = None
_missing_capture_enrichment_columns: set[str] = set()
_ENRICHMENT_COLUMNS = {"session_id", "reference_matches", "reference_explanation"}


def _load_taxonomy() -> list[dict]:
    global _taxonomy_cache
    if _taxonomy_cache is not None:
        return _taxonomy_cache
    response = (
        supabase.table("taxonomy")
        .select("id, label, domain, embedding, embedding_model")
        .eq("domain", CLASSIFICATION_DOMAIN)
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise RuntimeError(
            "Taxonomy is empty for domain "
            f"'{CLASSIFICATION_DOMAIN}'. Run sakad-backend/scripts/seed_taxonomy.py."
        )

    parsed = []
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
            "Taxonomy rows are missing embeddings for domain "
            f"'{CLASSIFICATION_DOMAIN}'. Run sakad-backend/scripts/seed_taxonomy.py."
        )
    _taxonomy_cache = parsed
    return _taxonomy_cache


def generate_reference_explanation(
    taxonomy_matches: list[dict] | None,
    reference_matches: list[dict] | None,
    layer1_tags: list[str] | None = None,
    layer2_tags: list[str] | None = None,
) -> str | None:
    if not taxonomy_matches or not reference_matches:
        return None

    top_taxonomy = taxonomy_matches[0].get("label") or "the current taxonomy result"
    top_reference = reference_matches[0]
    reference_name = top_reference.get("title") or top_reference.get("designer") or "the top reference"
    cue_source = layer2_tags or layer1_tags or []
    cues = ", ".join(cue_source[:3])

    explanation = f"This image reads closest to {top_taxonomy} and aligns with {reference_name}."
    if cues:
        explanation += f" Key visual cues include {cues}."
    return explanation


def _build_capture_insert_payload(
    *,
    public_url: str,
    session_id: str | None,
    image_embedding: list[float],
    taxonomy_matches: list[dict],
    layer1: list[str],
    layer2: list[str],
    palette: list[str],
    reference_matches: list[dict],
    reference_explanation: str | None,
    include_enrichment: bool,
) -> dict:
    payload = {
        "image_url": public_url,
        "embedding": image_embedding,
        "taxonomy_matches": taxonomy_matches,
        "layer1_tags": layer1 or None,
        "layer2_tags": layer2 or None,
        "tags": {"palette": palette},
    }
    if include_enrichment:
        if "session_id" not in _missing_capture_enrichment_columns:
            payload["session_id"] = session_id
        if "reference_matches" not in _missing_capture_enrichment_columns:
            payload["reference_matches"] = reference_matches
        if "reference_explanation" not in _missing_capture_enrichment_columns:
            payload["reference_explanation"] = reference_explanation
    return payload


def _missing_enrichment_columns(exc: Exception) -> set[str]:
    message = str(exc).lower()
    schema_error = (
        ("column" in message and "does not exist" in message)
        or ("schema cache" in message and "column" in message)
    )
    if not schema_error:
        return set()
    return {column for column in _ENRICHMENT_COLUMNS if column in message}


def _insert_capture(payload: dict, *, allow_retry_without_enrichment: bool) -> object:
    global _missing_capture_enrichment_columns

    try:
        return supabase.table("captures").insert(payload).execute()
    except Exception as exc:
        missing_columns = _missing_enrichment_columns(exc)
        if not allow_retry_without_enrichment or not missing_columns:
            raise
        _missing_capture_enrichment_columns.update(missing_columns)
        logger.warning(
            "[capture] enrichment columns unavailable; retrying legacy insert shape: %s",
            exc,
        )
        retry_payload = {
            key: value
            for key, value in payload.items()
            if key not in missing_columns
        }
        return supabase.table("captures").insert(retry_payload).execute()


def _classify(
    image_embedding: list[float],
    text_embedding: list[float] | None,
) -> list[dict]:
    taxonomy = _load_taxonomy()
    img_vec = np.array(image_embedding, dtype=np.float32)

    if text_embedding is not None:
        txt_vec = np.array(text_embedding, dtype=np.float32)
        blended = IMAGE_WEIGHT * img_vec + TEXT_WEIGHT * txt_vec
        norm = np.linalg.norm(blended)
        blended = blended / norm if norm > 0 else img_vec
    else:
        blended = img_vec

    text_matrix = np.stack([row["embedding"] for row in taxonomy])
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
async def capture(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
) -> dict:
    try:
        image_bytes = await file.read()

        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"

        storage_response = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=filename,
            file=image_bytes,
            file_options={"content-type": file.content_type or "image/jpeg"},
        )
        if hasattr(storage_response, "error") and storage_response.error:
            logger.error("[capture] storage upload failed: %s", storage_response.error)
            raise HTTPException(
                status_code=500,
                detail=f"Storage upload failed: {storage_response.error}",
            )

        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)

        loop = asyncio.get_running_loop()
        image_embedding = await loop.run_in_executor(None, get_image_embedding, image_bytes)

        layer1_fn = functools.partial(
            get_layer1_tags_with_model,
            image_bytes,
            mime_type=file.content_type or "image/jpeg",
        )
        layer1, layer1_model = await loop.run_in_executor(None, layer1_fn)
        if not layer1:
            logger.warning("[capture] gemini layer1 unavailable; continuing with fallback path")

        if layer1:
            layer2_fn = functools.partial(
                get_layer2_tags_with_model,
                image_bytes,
                layer1,
                mime_type=file.content_type or "image/jpeg",
            )
            layer2, layer2_model = await loop.run_in_executor(None, layer2_fn)
        else:
            layer2 = []
            layer2_model = None
        if layer1 and not layer2:
            logger.warning("[capture] gemini layer2 unavailable; continuing with fallback path")

        if TEXT_WEIGHT > 0.0 and (layer1 or layer2):
            enriched_text = " ".join(layer1 + layer2)
            try:
                text_embedding: list[float] | None = await loop.run_in_executor(
                    None, get_text_embedding, enriched_text
                )
            except Exception as exc:
                logger.warning("[capture] text embedding failed; falling back to image-only: %s", exc)
                text_embedding = None
        else:
            text_embedding = None

        try:
            taxonomy_matches = _classify(image_embedding, text_embedding)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        reference_matches = get_reference_matches(image_embedding)
        palette = _extract_palette(image_bytes)

        try:
            reference_explanation = generate_reference_explanation(
                taxonomy_matches,
                reference_matches,
                layer1_tags=layer1 or None,
                layer2_tags=layer2 or None,
            )
        except Exception:
            logger.exception("[capture] reference explanation failed")
            reference_explanation = None

        insert_payload = _build_capture_insert_payload(
            public_url=public_url,
            session_id=session_id,
            image_embedding=image_embedding,
            taxonomy_matches=taxonomy_matches,
            layer1=layer1,
            layer2=layer2,
            palette=palette,
            reference_matches=reference_matches,
            reference_explanation=reference_explanation,
            include_enrichment=True,
        )
        insert_response = _insert_capture(
            insert_payload,
            allow_retry_without_enrichment=bool(_ENRICHMENT_COLUMNS & set(insert_payload)),
        )

        if not insert_response.data:
            logger.error("[capture] insert failed after successful processing")
            raise HTTPException(status_code=500, detail="Failed to insert capture record")

        capture_record = insert_response.data[0]
        logger.info(
            "[capture] success: id=%s taxonomy_matches=%s reference_matches=%s gemini_layer1=%s gemini_layer2=%s layer1_model=%s layer2_model=%s",
            capture_record.get("id"),
            len(taxonomy_matches),
            len(reference_matches),
            bool(layer1),
            bool(layer2),
            layer1_model,
            layer2_model,
        )
        capture_record["gemini_models"] = {
            "layer1": layer1_model,
            "layer2": layer2_model,
        }
        return capture_record
    except HTTPException:
        logger.exception("[capture] request failed")
        raise
    except Exception:
        logger.exception("[capture] unhandled failure")
        raise
