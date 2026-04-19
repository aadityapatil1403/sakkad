import ast
import logging

import numpy as np

from services.supabase_client import supabase

logger = logging.getLogger(__name__)

REFERENCE_CORPUS_TABLE = "reference_corpus"

_reference_cache: list[dict] | None = None
_reference_corpus_available = True


def _parse_embedding(raw_embedding: object) -> np.ndarray | None:
    if raw_embedding is None:
        return None
    try:
        embedding = ast.literal_eval(raw_embedding) if isinstance(raw_embedding, str) else raw_embedding
        vector = np.array(embedding, dtype=np.float32)
    except (SyntaxError, TypeError, ValueError) as exc:
        logger.warning("[retrieval] skipping malformed embedding: %s", exc)
        return None
    if vector.ndim != 1 or vector.size == 0:
        logger.warning("[retrieval] skipping malformed embedding shape: %s", getattr(vector, "shape", None))
        return None
    return vector


def _load_reference_corpus() -> list[dict]:
    global _reference_cache, _reference_corpus_available
    if _reference_cache is not None:
        return _reference_cache
    if not _reference_corpus_available:
        return []

    try:
        response = (
            supabase.table(REFERENCE_CORPUS_TABLE)
            .select("id, designer, brand, collection_or_era, title, description, image_url, embedding")
            .execute()
        )
    except Exception as exc:
        _reference_corpus_available = False
        _reference_cache = []
        logger.warning("[retrieval] reference corpus unavailable; disabling retrieval: %s", exc)
        return []

    parsed_rows = []
    for row in response.data or []:
        embedding = _parse_embedding(row.get("embedding"))
        if embedding is None:
            continue
        parsed_rows.append({
            "id": row.get("id"),
            "designer": row.get("designer"),
            "brand": row.get("brand"),
            "collection_or_era": row.get("collection_or_era"),
            "title": row.get("title"),
            "description": row.get("description"),
            "image_url": row.get("image_url"),
            "embedding": embedding,
        })

    _reference_cache = parsed_rows
    if not _reference_cache:
        logger.info("[retrieval] empty reference corpus")
    return _reference_cache


def get_reference_matches(image_embedding: list[float], limit: int = 5) -> list[dict]:
    if limit <= 0:
        return []

    corpus = _load_reference_corpus()
    if not corpus:
        logger.info("[retrieval] empty-hit: no corpus rows available")
        return []

    try:
        image_vec = np.array(image_embedding, dtype=np.float32)
    except (TypeError, ValueError) as exc:
        logger.warning("[retrieval] invalid query embedding: %s", exc)
        return []

    if image_vec.ndim != 1 or image_vec.size == 0:
        logger.warning("[retrieval] invalid query embedding shape: %s", getattr(image_vec, "shape", None))
        return []

    query_norm = np.linalg.norm(image_vec)
    if query_norm == 0:
        logger.warning("[retrieval] zero-norm query embedding")
        return []

    scored_rows = []
    for row in corpus:
        candidate_vec = row["embedding"]
        if candidate_vec.shape != image_vec.shape:
            logger.warning(
                "[retrieval] skipping row with mismatched embedding shape: id=%s query=%s row=%s",
                row.get("id"),
                image_vec.shape,
                candidate_vec.shape,
            )
            continue

        candidate_norm = np.linalg.norm(candidate_vec)
        if candidate_norm == 0:
            logger.warning("[retrieval] skipping zero-norm corpus embedding: id=%s", row.get("id"))
            continue

        score = float(np.dot(candidate_vec, image_vec) / (candidate_norm * query_norm))
        scored_rows.append({
            "id": row.get("id"),
            "designer": row.get("designer"),
            "brand": row.get("brand"),
            "collection_or_era": row.get("collection_or_era"),
            "title": row.get("title"),
            "description": row.get("description"),
            "image_url": row.get("image_url"),
            "score": round(score, 4),
        })

    if not scored_rows:
        logger.info("[retrieval] empty-hit: no usable reference matches")
        return []

    scored_rows.sort(key=lambda row: row["score"], reverse=True)
    return scored_rows[:limit]
